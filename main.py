import argparse

import libcst as cst
from visitors import AttrDecoratorVisitor
from visitors import DangerousFunctionVisitor
from visitors import FunctionArgAssignVisitor
from visitors import LambdaVisitor
from visitors import NestedFunctionVisitor


def run_evals(code: str, file_name: str) -> None:
    tree = cst.parse_module(code)
    visitors = [
        DangerousFunctionVisitor(),
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
            # print(violation.log_message(code_lines))
            print(f"{file_name}:{violation.format()}")

            """
            pylint format is:
            {filename}:{line_number}:{column_number}: {error_code}: {message} ({symbol})
            """


def main(args: argparse.Namespace) -> None:
    if args.file:
        with open(args.file, "r") as file:
            lines = file.readlines()
            source_code = "".join(lines)
        print("Source code:")
        print("-" * 80)
        for idx, line in enumerate(lines):
            print("{:4d} | {}".format(idx + 1, line), end="")
        print("-" * 80)
        run_evals(source_code, args.file)
    else:
        print("Please specify a file path using --file argument.")


if __name__ == "__main__":
    # run like: python main.py --file "path/to/file.py"
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, help="Path to the file to be checked")
    args = parser.parse_args()

    main(args)
