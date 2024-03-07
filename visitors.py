from abc import ABC
from dataclasses import dataclass

import libcst as cst
from libcst import matchers as m
from libcst.metadata import PositionProvider
from style_violation import StyleViolation
from violation_error_codes import ViolationErrorCode


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
    Only two attr decorators allowed:
    @attr.s(auto_attribs=True, frozen=True)

    and
    @attr.s(auto_attribs=True)
    """

    # def visit_ClassDef_decorators(self, node: cst.Attribute):
    #     code_range = self.get_metadata(PositionProvider, node)
    #     self.violations.append(
    #         StyleViolation(
    #             name="Attribute",
    #             line_number=start_line_num,
    #             message=f"Attribute found at line: {start_line_num}",
    #         )
    #     )
    pass
