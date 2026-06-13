from unittest import TestCase

from scout.dedup import canonical_key


class CanonicalKeyTests(TestCase):
    def test_combines_name_conference_year(self):
        c = {
            "benchmark_name": "ImageNet-21K-P",
            "conference": "NeurIPS",
            "year": 2025,
        }
        self.assertEqual(canonical_key(c), "imagenet-21k-p|neurips|2025")

    def test_lowercases_name_and_conference(self):
        c = {
            "benchmark_name": "FOO",
            "conference": "BAR",
            "year": 2024,
        }
        self.assertEqual(canonical_key(c), "foo|bar|2024")

    def test_strips_whitespace(self):
        c = {
            "benchmark_name": "  imagenet  ",
            "conference": " neurips ",
            "year": 2025,
        }
        self.assertEqual(canonical_key(c), "imagenet|neurips|2025")

    def test_year_is_stringified_as_int(self):
        c = {
            "benchmark_name": "x",
            "conference": "y",
            "year": 2025,
        }
        self.assertTrue(canonical_key(c).endswith("|2025"))

    def test_pipe_in_fields_does_not_cause_collision(self):
        # Without escaping, ("a|b", "c") and ("a", "b|c") would both join to
        # "a|b|c|2025" and collide. The escaped form keeps them distinct.
        a = canonical_key(
            {"benchmark_name": "a|b", "conference": "c", "year": 2025}
        )
        b = canonical_key(
            {"benchmark_name": "a", "conference": "b|c", "year": 2025}
        )
        self.assertNotEqual(a, b)

    def test_backslash_in_fields_does_not_create_collision(self):
        # The escape itself must also be injective: a literal backslash in
        # one field can't be confused with the escape sequence for `|`.
        a = canonical_key(
            {"benchmark_name": "a\\", "conference": "|b", "year": 2025}
        )
        b = canonical_key(
            {"benchmark_name": "a", "conference": "\\|b", "year": 2025}
        )
        self.assertNotEqual(a, b)
