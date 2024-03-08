from abc import ABC
from dataclasses import dataclass

import attr
import libcst as cst
from cstlint.style_violation import StyleViolation
from cstlint.violation_error_codes import ViolationErrorCode
from libcst import matchers as m
from libcst.metadata import PositionProvider


@dataclass
class FunctionInfo:
    name: str
    arg_names: list[str]

    def contains_arg(self, arg: str) -> bool:
        return arg in self.args


def extract_value_from_assign_target(target: cst.AssignTarget) -> str:
    # TODO: maybe a better way to extract the underlying
    # var name/value out of an AssingTarget node
    if isinstance(target.target, cst.Name):
        return target.target.value
    elif isinstance(target.target, cst.Subscript):
        return target.target.value.value
    elif isinstance(target.target, cst.Attribute):
        return target.target.value.value
    else:
        return None

    raise ValueError(f"Unsupported assign target type: {target}")


class StyleViolationsVisitor(cst.CSTVisitor, ABC):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self):
        super().__init__()
        self.violations = []

    def get_node_line_info(self, node: cst.CSTNode) -> tuple[int, int, int, int]:
        code_range = self.get_metadata(PositionProvider, node)
        return (
            code_range.start.line,
            code_range.start.column,
            code_range.end.line,
            code_range.end.column,
        )

    @classmethod
    def parse_and_evaluate_violations(cls, source_code: str) -> list[StyleViolation]:
        tree = cst.parse_module(source_code)
        wrapper = cst.MetadataWrapper(tree)
        visitor = cls()
        wrapper.visit(visitor)
        return visitor.violations


class DangerousFunctionVisitor(StyleViolationsVisitor):
    VIOLATION_ERROR_CODE = ViolationErrorCode.DANGEROUS_FUNCTION

    def visit_Call(self, node: cst.Call):
        code_range = self.get_metadata(PositionProvider, node)

        if isinstance(node.func, cst.Name) and node.func.value in [
            "eval",
            "exec",
            "getattr",
            "setattr",
        ]:
            self.violations.append(
                StyleViolation(
                    error_code=self.VIOLATION_ERROR_CODE,
                    code_range=code_range,
                )
            )


class NestedFunctionVisitor(StyleViolationsVisitor):
    VIOLATION_ERROR_CODE = ViolationErrorCode.NESTED_FUNCTION

    def __init__(self):
        super().__init__()
        self.function_stack = []

    def visit_FunctionDef(self, node: cst.FunctionDef):
        code_range = self.get_metadata(PositionProvider, node)

        if len(self.function_stack) > 0:
            self.violations.append(
                StyleViolation(
                    error_code=self.VIOLATION_ERROR_CODE,
                    code_range=code_range,
                )
            )

        self.function_stack.append(node)

    def leave_FunctionDef(self, node: cst.FunctionDef):
        self.function_stack.pop()


class FunctionArgAssignVisitor(StyleViolationsVisitor):
    VIOLATION_ERROR_CODE = ViolationErrorCode.FUNCTION_ARG_ASSIGN

    def __init__(self):
        super().__init__()
        self.function_stack = []

    # TODO: not very DRY but not that much time so I'll leave it as is
    def visit_AugAssign(self, node: cst.AugAssign) -> None:
        if not self.function_stack:
            return
        if self.function_stack[-1].name in ["__init__", "__new__"]:
            return

        code_range = self.get_metadata(PositionProvider, node)
        current_function = self.function_stack[-1]
        assign_target = node.target.value
        assign_target = extract_value_from_assign_target(node)
        if assign_target in current_function.arg_names:
            self.violations.append(
                StyleViolation(
                    error_code=self.VIOLATION_ERROR_CODE,
                    code_range=code_range,
                )
            )

    def visit_Assign_targets(self, node: cst.Assign):
        """
        Detect if a variable being assigned to as one of the arguments
        """
        if not self.function_stack:
            return

        if self.function_stack[-1].name in ["__init__", "__new__"]:
            return

        code_range = self.get_metadata(PositionProvider, node)
        current_function = self.function_stack[-1]

        for target in node.targets:
            assign_target = extract_value_from_assign_target(target)

            if assign_target in current_function.arg_names:
                self.violations.append(
                    StyleViolation(
                        error_code=self.VIOLATION_ERROR_CODE,
                        code_range=code_range,
                    )
                )

    def visit_FunctionDef(self, node: cst.FunctionDef):
        fn_args = []
        for param in node.params.params:
            fn_args.append(param.name.value)

        fn_info = FunctionInfo(
            name=node.name.value,
            arg_names=fn_args,
        )

        self.function_stack.append(fn_info)

    def leave_FunctionDef(self, node: cst.FunctionDef):
        self.function_stack.pop()


class LambdaVisitor(StyleViolationsVisitor):
    VIOLATION_ERROR_CODE = ViolationErrorCode.LAMBDA

    def visit_Lambda(self, node: cst.Lambda):
        code_range = self.get_metadata(PositionProvider, node)
        self.violations.append(
            StyleViolation(
                error_code=self.VIOLATION_ERROR_CODE,
                code_range=code_range,
            )
        )


class MutableDefaultArgVisitor(StyleViolationsVisitor):
    VIOLATION_ERROR_CODE = ViolationErrorCode.MUTABLE_DEFAULT_ARG

    def visit_FunctionDef(self, node: cst.FunctionDef):
        for param in node.params.params:
            if param.default is not None:
                if isinstance(param.default, (cst.List, cst.Dict, cst.Set)):
                    code_range = self.get_metadata(PositionProvider, node)
                    self.violations.append(
                        StyleViolation(
                            error_code=self.VIOLATION_ERROR_CODE,
                            code_range=code_range,
                        )
                    )

                # Alternatively, using matchers for more complex checks
                elif m.matches(param.default, m.List() | m.Dict() | m.Set()):
                    code_range = self.get_metadata(PositionProvider, param.default)
                    self.violations.append(
                        StyleViolation(
                            error_code=self.VIOLATION_ERROR_CODE,
                            code_range=code_range,
                        )
                    )


class AttrDecoratorVisitor(StyleViolationsVisitor):
    """
    From the style guide:
        Only two attr decorators allowed:
        @attr.s(auto_attribs=True, frozen=True)
        @attr.s(auto_attribs=True)
        - therefore auto_attribs must be true

        `kw_only=True` and `repr=False` are currently the only permitted additional attrs fields.

    Therefore, this visitor checks:
    - check that a @attr.s decorator only uses keywords: auto_attribs, frozen, kw_only, repr
    - auto_attribs must be present and must be True
    - kw_only (if present) must be True
    - repr (if present) must be False
    """

    def _validate_attrs_args(self):
        pass

    def visit_ClassDef_decorators(self, node: cst.Call):
        code_range = self.get_metadata(PositionProvider, node)

        for decorator in node.decorators:
            decorator_name = decorator.decorator.func.value
            if decorator_name.value != "attr":
                continue

            assert decorator.decorator.func.attr.value == "s"

            for arg in decorator.decorator.args:
                if arg.keyword.value not in [
                    "auto_attribs",
                    "frozen",
                    "kw_only",
                    "repr",
                ]:
                    self.violations.append(
                        StyleViolation(
                            error_code=ViolationErrorCode.ATTR_DECORATOR,
                            code_range=code_range,
                        )
                    )

                if arg.keyword.value == "auto_attribs" and arg.value.value != "True":
                    self.violations.append(
                        StyleViolation(
                            error_code=ViolationErrorCode.ATTR_DECORATOR,
                            code_range=code_range,
                        )
                    )

                if arg.keyword.value == "kw_only" and arg.value.value != "True":
                    self.violations.append(
                        StyleViolation(
                            error_code=ViolationErrorCode.ATTR_DECORATOR,
                            code_range=code_range,
                        )
                    )

                if arg.keyword.value == "repr" and arg.value.value != "False":
                    self.violations.append(
                        StyleViolation(
                            error_code=ViolationErrorCode.ATTR_DECORATOR,
                            code_range=code_range,
                        )
                    )
