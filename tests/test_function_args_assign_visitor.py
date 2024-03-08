import unittest

from cstlint.visitors import FunctionArgAssignVisitor


class TestFunctionArgsVisitor(unittest.TestCase):

    TEST_CASES = [
        ("def f(lst):\n    lst[0] = 1", 1),
        ("def f(x):\n    x += 10", 1),
        ("def f(x):\n    x -= 10", 1),
        ("def f(x):\n    x *= 10", 1),
        ("def f(x):\n    x /= 10", 1),
        ("def f(x, y):\n    y += 10", 1),
        ("def f(x, y):\n    y.value += 10", 1),
    ]

    def test_usage(self):
        for source_code, expected_violation_count in self.TEST_CASES:
            with self.subTest(source_code=source_code):
                violations = FunctionArgAssignVisitor.parse_and_evaluate_violations(
                    source_code
                )
                self.assertEqual(len(violations), expected_violation_count)


if __name__ == "__main__":
    unittest.main()
