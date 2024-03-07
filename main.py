import logging
from dataclasses import dataclass
from typing import Any

import attrs
import libcst as cst
from libcst.metadata import PositionProvider

logging.basicConfig(level=logging.INFO, format="[%(levelname)s][%(name)s] %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class StyleViolation:
    name: str
    line_number: int
    message: str


@dataclass
class FunctionInfo:
    name: str
    arg_names: list[Any]

    def contains_arg(self, arg: str) -> bool:
        return arg in self.args


def value_from_assign_target(target: cst.AssignTarget) -> str:
    # TODO: maybe a better way to extract the underlying
    # var name/value out of an AssingTarget node
    if isinstance(target.target, cst.Name):
        return target.target.value
    elif isinstance(target.target, cst.Subscript):
        return target.target.value.value
    elif isinstance(target.target, cst.Attribute):
        return target.target.value.value
    raise ValueError(f"Unsupported assign target type: {target}")


class StyleViolationsVisitor(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self):
        super().__init__()
        self.violations = []


class EvalExecVisitor(StyleViolationsVisitor):

    def visit_Call(self, node: cst.Call):
        # Check if the call is a Name node and matches 'eval', 'getattr', or 'setattr'
        code_range = self.get_metadata(PositionProvider, node)
        start_line_num = code_range.start.line

        if isinstance(node.func, cst.Name) and node.func.value in [
            "eval",
            "exec",
            "getattr",
            "setattr",
        ]:
            self.violations.append(
                StyleViolation(
                    name="Invalid function used",
                    line_number=start_line_num,
                    message=f"Dangerous call found: {node.func.value}",
                )
            )


class NestedFunctionVisitor(StyleViolationsVisitor):
    def __init__(self):
        super().__init__()
        self.function_stack = []

    def visit_FunctionDef(self, node: cst.FunctionDef):
        code_range = self.get_metadata(PositionProvider, node)
        start_line_num = code_range.start.line
        fname = node.name.value

        if len(self.function_stack) > 0:
            parent_name = self.function_stack[-1].name.value
            msg = f"Function {fname} defined within {parent_name}"
            self.violations.append(
                StyleViolation("Nested function", start_line_num, msg)
            )

        self.function_stack.append(node)

    def leave_FunctionDef(self, node: cst.FunctionDef):
        self.function_stack.pop()


class FunctionArgAssignVisitor(StyleViolationsVisitor):
    def __init__(self):
        super().__init__()
        self.function_stack = []

    def visit_Assign_targets(self, node: cst.Assign):
        """
        Detect if a variable being assigned to as one of the arguments
        """
        code_range = self.get_metadata(PositionProvider, node)
        start_line_num = code_range.start.line
        current_function = self.function_stack[-1]

        for target in node.targets:
            assign_target = value_from_assign_target(target)

            if assign_target in current_function.arg_names:
                fn_name = current_function.name
                value = value_from_assign_target(target)
                self.violations.append(
                    StyleViolation(
                        name="Assign to function arg",
                        line_number=start_line_num,
                        message=f"Function {fn_name} arg {value} is being modified",
                    )
                )

    def visit_FunctionDef(self, node: cst.FunctionDef):
        code_range = self.get_metadata(PositionProvider, node)
        start_line_num = code_range.start
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
    def visit_Lambda(self, node: cst.Lambda):
        code_range = self.get_metadata(PositionProvider, node)
        start_line_num = code_range.start.line
        self.violations.append(
            StyleViolation(
                name="Lambda",
                line_number=start_line_num,
                message=f"Lambda found at line: {start_line_num}",
            )
        )


class AttrDecoratorVisitor(StyleViolationsVisitor):
    """
    two attr decorators allowed:
    @attr.s(auto_attribs=True, frozen=True)

    and
    @attr.s(auto_attribs=True)
    """

    # def visit_ClassDef_decorators(self, node: cst.Attribute):
    #     code_range = self.get_metadata(PositionProvider, node)
    #     start_line_num = code_range.start.line

    #     self.violations.append(
    #         StyleViolation(
    #             name="Attribute",
    #             line_number=start_line_num,
    #             message=f"Attribute found at line: {start_line_num}",
    #         )
    #     )

    def visit_ClassDef(self, node: cst.ClassDef) -> None:
        # Check for @attr.s decorator
        for decorator in node.decorators:
            if isinstance(decorator.decorator, cst.Call) and isinstance(decorator.decorator.func, cst.Name):
                decorator_name = decorator.decorator.func.value
                if decorator_name == "attr.s":
                    self._check_attrs_usage(decorator.decorator, node)



def run_evals(code: str):
    code_lines = code.split("\n")
    tree = cst.parse_module(code)
    visitors = [
        EvalExecVisitor(),
        NestedFunctionVisitor(),
        LambdaVisitor(),
        FunctionArgAssignVisitor(),
        AttrDecoratorVisitor(),
    ]
    wrapper = cst.MetadataWrapper(tree)

    for visitor in visitors:
        wrapper.visit(visitor)

    for visitor in visitors:
        for violation in visitor.violations:
            print(f"{violation} | Line: {code_lines[violation.line_number - 1]}")


if __name__ == "__main__":
    source = """
def set_value(a, b, c):
    a = 10
    b[10] = 0
    c.x = 100
    d[0] += 30

def a():
    def b():
        return 10
    return b()
eval("1+1")


@attrs.s(auto_attribs=True, frozen=True)
class MyData:
    x: int
    y: str
"""
    # visitor = check_style(source)
    run_evals(source)
