import logging

import libcst as cst
from visitors import AttrDecoratorVisitor
from visitors import EvalExecVisitor
from visitors import FunctionArgAssignVisitor
from visitors import LambdaVisitor
from visitors import NestedFunctionVisitor


logging.basicConfig(level=logging.INFO, format="[%(levelname)s][%(name)s] %(message)s")
logger = logging.getLogger(__name__)


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
