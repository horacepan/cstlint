from enum import Enum


class ViolationErrorCode(Enum):
    DANGEROUS_FUNCTION = (
        "E1001",
        "Use of dangerous function (eval, exec, getattr, setattr) is discouraged.",
    )
    NESTED_FUNCTION = (
        "E1002",
        "Definition of a function within another function is discouraged.",
    )
    LAMBDA = (
        "E1003",
        "Use of lambda functions is discouraged in favor of named functions.",
    )
    FUNCTION_ARG_ASSIGN = (
        "E1004",
        "Assignment to function arguments within the function body is discouraged.",
    )
    ATTR_DECORATOR = ("E1005", "Incorrect usage of @attr.s decorator detected.")
    MUTABLE_DEFAULT_ARG = ("E1006", "Use of mutable default argument is discouraged.")

    def __init__(self, code, message):
        self.code = code
        self.message = message

    @property
    def error_code(self):
        return self.value[0]

    @property
    def error_message(self) -> str:
        return self.value[1]
