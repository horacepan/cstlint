import unittest

from cstlint.visitors import DangerousFunctionVisitor


class TestDangerousFunctionsVisitor(unittest.TestCase):

    TEST_CASES = [
        ("exec('print(1)')", 1),
        ("eval('print(1)')", 1),
        ("getattr([], '__len__')", 1),
        ("setattr(x, 'eval'); eval('1+2')", 2),
        ("evaluate(10)", 0),
        ("getattr = 0", 0),
        ("setattr = 1", 0),
    ]

    def test_usage(self):
        for source_code, expected_violation_count in self.TEST_CASES:
            with self.subTest(source_code=source_code):
                violations = DangerousFunctionVisitor.parse_and_evaluate_violations(
                    source_code
                )
                self.assertEqual(len(violations), expected_violation_count)


if __name__ == "__main__":
    unittest.main()
