from dataclasses import dataclass

from libcst._position import CodeRange
from violation_error_codes import ViolationErrorCode


@dataclass
class StyleViolation:
    error_code: ViolationErrorCode
    code_range: CodeRange

    @property
    def column_number(self):
        return self.code_range.start.column

    @property
    def line_number(self):
        return self.code_range.start.line

    def format(self):
        error_code = self.error_code.error_code
        error_message = self.error_code.error_message
        return f"{self.line_number}:{self.column_number}: {error_code}: {error_message}"

    def log_message(self, source_code: str) -> str:
        start_line = self.code_range.start.line
        violating_code_line = source_code[start_line - 1]
        return "".join(
            [
                f"Line: {start_line:4d} | ",
                f": {violating_code_line}",
            ]
        )
