import logging

import libcst as cst
from libcst.metadata import ParentNodeProvider
from libcst.metadata import PositionProvider

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StyleGuideCheckerVisitor(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (ParentNodeProvider, PositionProvider)

    def __init__(self):
        super().__init__()
        self.inline_functions = []

    def visit_FunctionDef(self, node: cst.FunctionDef):
        parent = self.get_metadata(ParentNodeProvider, node)
        code_range = self.get_metadata(PositionProvider, node)
        start_line_num = code_range.start

        # Just checks that the parent is is a function too
        # TODO: check ancestors
        if isinstance(parent, cst.FunctionDef):
            logger.info(f"Inline function found at line: {start_line_num}")

    def visit_Lambda(self, node: cst.Lambda):
        code_range = self.get_metadata(PositionProvider, node)
        start_line_num = code_range.start.line
        self.inline_functions.append(("Lambda", start_line_num))
        logger.info(f"Lambda found at line: {start_line_num}")


def check_style(code: str):
    tree = cst.parse_module(code)
    wrapper = cst.MetadataWrapper(tree)
    visitor = StyleGuideCheckerVisitor()
    wrapper.visit(visitor)
    return visitor


if __name__ == "__main__":
    source = """
def outer_function():
    x = lambda z: z + 10
    return x(5)

z = lambda t: t+10
"""
    visitor = check_style(source)
