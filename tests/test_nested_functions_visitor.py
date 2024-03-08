import unittest

from cstlint.visitors import NestedFunctionVisitor


class TestNestedFunctionsVisitor(unittest.TestCase):

    TEST_CASES = [
        ("def a():\n    def b():\n        pass", 1),
        ("def a():\n    def b():\n        def c():\n            pass", 2),
        ("if x > 0:\n    def b():\n        pass", 0),
        ("class Dog:\n    def __init__(self):\n        pass", 0),
    ]

    def test_usage(self):
        for source_code, expected_violation_count in self.TEST_CASES:
            with self.subTest(source_code=source_code):
                violations = NestedFunctionVisitor.parse_and_evaluate_violations(
                    source_code
                )
                self.assertEqual(len(violations), expected_violation_count)


if __name__ == "__main__":
    unittest.main()
