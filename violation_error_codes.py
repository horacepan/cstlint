from enum import Enum


# Dont feel great about the error code naming. Ideally
# want some autoincrementer. But also thought something
# that autoincremented might get messed up if someone
# reordered the enum entries accidentally.
class ViolationErrorCode(Enum):
    DANGEROUS_FUNCTION = (
        "S1001",
        "Use of dangerous function (eval, exec, getattr, setattr) is discouraged.",
    )
    NESTED_FUNCTION = (
        "S1002",
        "Definition of a function within another function is discouraged.",
    )
    LAMBDA = (
        "S1003",
        "Use of lambda functions is discouraged in favor of named functions.",
    )
    FUNCTION_ARG_ASSIGN = (
        "S1004",
        "Assignment to function arguments within the function body is discouraged.",
    )
    ATTR_DECORATOR = ("S1005", "Incorrect usage of @attr.s decorator detected.")
    MUTABLE_DEFAULT_ARG = ("S1006", "Use of mutable default argument is discouraged.")

    def __init__(self, code, message):
        self.code = code
        self.message = message

    @property
    def error_code(self):
        return self.value[0]

    @property
    def error_message(self) -> str:
        return self.value[1]
