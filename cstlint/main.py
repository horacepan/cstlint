import argparse

import libcst as cst
from cstlint.visitors import AttrDecoratorVisitor
from cstlint.visitors import DangerousFunctionVisitor
from cstlint.visitors import FunctionArgAssignVisitor
from cstlint.visitors import LambdaVisitor
from cstlint.visitors import MutableDefaultArgVisitor
from cstlint.visitors import NestedFunctionVisitor


def run_style_checks(code: str, file_name: str) -> None:
    tree = cst.parse_module(code)
    visitors = [
        DangerousFunctionVisitor(),
        NestedFunctionVisitor(),
        LambdaVisitor(),
        FunctionArgAssignVisitor(),
        AttrDecoratorVisitor(),
        MutableDefaultArgVisitor(),
    ]
    wrapper = cst.MetadataWrapper(tree)

    for visitor in visitors:
        wrapper.visit(visitor)

    for visitor in visitors:
        for violation in visitor.violations:
            print(f"{file_name}:{violation.format()}")
            """
            mimic pylint format which is:
            {filename}:{line_number}:{column_number}: {error_code}: {standard error message}
            """


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=str, help="Path to the file to be checked")
    args = parser.parse_args()

    if args.file:
        with open(args.file, "r") as file:
            lines = file.readlines()
            source_code = "".join(lines)
        print("Source code:")
        print("-" * 80)
        for idx, line in enumerate(lines):
            print("{:4d} | {}".format(idx + 1, line), end="")
        print("-" * 80)

        run_style_checks(source_code, args.file)
    else:
        print("Please specify a file path using --file argument.")


if __name__ == "__main__":
    main()
