import unittest

from cstlint.visitors import MutableDefaultArgVisitor


"""
def f(x: list[int] = []):
    pass
"""


class TestFunctionArgsVisitor(unittest.TestCase):

    TEST_CASES = [
        ("def f(x: list[int] = [], y: dict[Any, Any] = {}):\n    pass", 2),
        ("def f(x: list[int] = [1, 2, 3]):\n    pass", 1),
        ("def f(x: dict[int, int] = {1: 0}):\n    pass", 1),
        (
            "class Animals:\n    def __init__(self, species: list[str] = []):\n        pass",
            1,
        ),
    ]

    def test_usage(self):
        for source_code, expected_violation_count in self.TEST_CASES:
            with self.subTest(source_code=source_code):
                violations = MutableDefaultArgVisitor.parse_and_evaluate_violations(
                    source_code
                )
                self.assertEqual(len(violations), expected_violation_count)


if __name__ == "__main__":
    unittest.main()
