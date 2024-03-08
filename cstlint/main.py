import argparse
import sys

import libcst as cst
from cstlint.visitors import AttrDecoratorVisitor
from cstlint.visitors import DangerousFunctionVisitor
from cstlint.visitors import FunctionArgAssignVisitor
from cstlint.visitors import LambdaVisitor
from cstlint.visitors import MutableDefaultArgVisitor
from cstlint.visitors import NestedFunctionVisitor


def find_and_print_style_violations(
    code: str, file_name: str, verbose: bool, quiet: bool = False
) -> None:
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
    code_lines = code.split("\n")

    for visitor in visitors:
        wrapper.visit(visitor)

    for visitor in visitors:
        for violation in visitor.violations:
            if quiet:
                print(f"{file_name}:{violation.format()}")
                sys.exit(1)
            if verbose:
                line = code_lines[violation.code_range.start.line - 1]
                print(f"{file_name}:{violation.format()}: {line}")
            else:
                print(f"{file_name}:{violation.format()}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=str, help="Path to the file to be checked")
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        help="Show violating line if set",
    )
    parser.add_argument(
        "--show-source",
        action="store_true",
        default=False,
        help="Show source code. Useful for debugging",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        default=False,
        help="Don't display anything and exit on first violation",
    )
    args = parser.parse_args()

    if args.file:
        with open(args.file, "r") as file:
            lines = file.readlines()
            source_code = "".join(lines)

        if args.show_source:
            print("Source code:")
            print("-" * 80)
            for idx, line in enumerate(lines):
                print("{:4d} | {}".format(idx + 1, line), end="")
            print("-" * 80)

        find_and_print_style_violations(
            source_code, args.file, args.verbose, args.quiet
        )
    else:
        print("Please specify a file path using --file argument.")


if __name__ == "__main__":
    main()
