import unittest

from cstlint.visitors import AttrDecoratorVisitor


class TestAttrDecoratorVisitor(unittest.TestCase):

    TEST_CASES = [
        (
            """
@attr.s(auto_attribs=True, frozen=False, kw_only=False)
class Dog:
    pass
""",
            1,
        ),
        (
            """
@attr.s(auto_attribs=True, frozen=False, repr=True)
class Dog:
    pass
""",
            1,
        ),
        (
            """
@attr.s(random=0, frozen=False, repr=True)
class Dog:
    pass
""",
            3,  # missing auto_attribs, repr not False, random is not a valid keyword
        ),
    ]

    def test_usage(self):
        for source_code, expected_violation_count in self.TEST_CASES:
            with self.subTest(source_code=source_code):
                violations = AttrDecoratorVisitor.parse_and_evaluate_violations(
                    source_code
                )
                self.assertEqual(len(violations), expected_violation_count)


if __name__ == "__main__":
    unittest.main()
