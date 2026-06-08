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
