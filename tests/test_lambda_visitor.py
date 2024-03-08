import unittest

from cstlint.visitors import LambdaVisitor


class TestLambdaVisitor(unittest.TestCase):

    TEST_CASES = [
        ("lambda x: x + 1", 1),
        ("def f():\n    x = lambda y: y + 1", 1),
    ]

    def test_lambda_usages(self):
        for source_code, expected_violation_count in self.TEST_CASES:
            with self.subTest(source_code=source_code):
                violations = LambdaVisitor.parse_and_evaluate_violations(source_code)
                self.assertEqual(len(violations), expected_violation_count)


if __name__ == "__main__":
    unittest.main()
