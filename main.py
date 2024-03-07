import logging
from dataclasses import dataclass
from typing import Any

import libcst as cst
from libcst.metadata import ParentNodeProvider
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


class EvalCheckerVisitor(cst.CSTVisitor):
    def __init__(self) -> None:
        super().__init__()
        self.dangerous_calls = []
        self.violations = []

    def visit_Call(self, node: cst.Call):
        # Check if the call is a Name node and matches 'eval', 'getattr', or 'setattr'
        if isinstance(node.func, cst.Name) and node.func.value in [
            "eval",
            "exec",
            "getattr",
            "setattr",
        ]:
            self.dangerous_calls.append((node.func.value, node))
            logger.info("Dangerous call found: %s", node.func.value)


class NestedFunctionVisitor(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (PositionProvider,)
    def __init__(self):
        self.function_stack = []
        self.violations = []

    def visit_FunctionDef(self, node: cst.FunctionDef):
        code_range = self.get_metadata(PositionProvider, node)
        start_line_num = code_range.start.line
        fname = node.name.value

        if len(self.function_stack) > 0:
            parent_name = self.function_stack[-1].name.value
            msg = f"Function {fname} defined within {parent_name}"
            self.violations.append(StyleViolation("Nested function", start_line_num, msg))

        self.function_stack.append(node)

    def leave_FunctionDef(self, node: cst.FunctionDef):
        self.function_stack.pop()

class StyleGuideCheckerVisitor(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (ParentNodeProvider, PositionProvider)

    def __init__(self, source_code: str):
        super().__init__()
        self.source_code_lines = source_code.splitlines()
        self.inline_functions = []
        self.args = {}
        self.assigned_targets = []
        self.function_stack = []
        self.function_args = []
        self.violations = []

    def visit_Assign_value(self, node: cst.Assign):
        """
        RHS of an assign statement
        """
        pass

    def visit_Assign_targets(self, node: cst.Assign):
        """
        Detect if a variable being assigned to as one of the arguments
        """
        code_range = self.get_metadata(PositionProvider, node)
        start_line_num = code_range.start.line

        for target in node.targets:
            assign_target = value_from_assign_target(target)
            self.assigned_targets.append(assign_target)

            if assign_target in self.function_stack[-1].arg_names:
                fn_name = self.function_stack[-1].name
                value = value_from_assign_target(target)
                logger.info(
                    f"Function {fn_name} arg {value} is being modified: {self.source_code_lines[start_line_num-1]}"
                )

    def visit_FunctionDef(self, node: cst.FunctionDef):
        parent = self.get_metadata(ParentNodeProvider, node)
        code_range = self.get_metadata(PositionProvider, node)
        start_line_num = code_range.start
        fn_args = []
        for param in node.params.params:
            fn_args.append(param.name.value)

        # Just checks that the parent is is a function too
        # TODO: check ancestors
        if isinstance(parent, cst.FunctionDef):
            logger.info(f"Inline function found at line: {start_line_num}")

        fn_info = FunctionInfo(
            name=node.name.value,
            arg_names=fn_args,
        )
        self.function_stack.append(fn_info)

    def leave_FunctionDef(self, node: cst.FunctionDef):
        self.function_stack.pop()

    def visit_Lambda(self, node: cst.Lambda):
        code_range = self.get_metadata(PositionProvider, node)
        start_line_num = code_range.start.line
        self.inline_functions.append(("Lambda", start_line_num))
        logger.info(f"Lambda found at line: {start_line_num}")


def check_style(code: str):
    tree = cst.parse_module(code)
    wrapper = cst.MetadataWrapper(tree)
    visitor = StyleGuideCheckerVisitor(code)
    wrapper.visit(visitor)
    return visitor


def check_eval(code: str):
    tree = cst.parse_module(code)
    wrapper = cst.MetadataWrapper(tree)
    visitor = EvalCheckerVisitor()
    wrapper.visit(visitor)
    return visitor

def run_evals(code: str):
    tree = cst.parse_module(code)
    visitors = [NestedFunctionVisitor()]
    wrapper = cst.MetadataWrapper(tree)

    for visitor in visitors:
        wrapper.visit(visitor)

    for visitor in visitors:
        for violation in visitor.violations:
            print(violation)

if __name__ == "__main__":
    source = """
def set_value(a, b, c):
    a = 10
    b[10] = 0
    c.x = 100
    d[0] += 30
"""
    source_eval = """
def a():
    def b():
        return 10
    return b()
"""
    # visitor = check_style(source)
    visitor = check_eval(source_eval)

    run_evals(source_eval)
