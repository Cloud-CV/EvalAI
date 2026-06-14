import re
from unittest import TestCase

from scout.dedup import canonical_key

HEX64 = re.compile(r"^[0-9a-f]{64}$")


class CanonicalKeyTests(TestCase):
    def test_returns_fixed_length_sha256_hex(self):
        c = {
            "benchmark_name": "ImageNet-21K-P",
            "conference": "NeurIPS",
            "year": 2025,
        }
        key = canonical_key(c)
        self.assertEqual(len(key), 64)
        self.assertRegex(key, HEX64)

    def test_is_deterministic(self):
        c = {
            "benchmark_name": "ImageNet-21K-P",
            "conference": "NeurIPS",
            "year": 2025,
        }
        self.assertEqual(canonical_key(c), canonical_key(c))

    def test_lowercases_name_and_conference(self):
        upper = {
            "benchmark_name": "FOO",
            "conference": "BAR",
            "year": 2024,
        }
        lower = {
            "benchmark_name": "foo",
            "conference": "bar",
            "year": 2024,
        }
        self.assertEqual(canonical_key(upper), canonical_key(lower))

    def test_strips_whitespace(self):
        padded = {
            "benchmark_name": "  imagenet  ",
            "conference": " neurips ",
            "year": 2025,
        }
        trimmed = {
            "benchmark_name": "imagenet",
            "conference": "neurips",
            "year": 2025,
        }
        self.assertEqual(canonical_key(padded), canonical_key(trimmed))

    def test_year_is_normalized_as_int(self):
        as_int = {
            "benchmark_name": "x",
            "conference": "y",
            "year": 2025,
        }
        as_str = {
            "benchmark_name": "x",
            "conference": "y",
            "year": "2025",
        }
        self.assertEqual(canonical_key(as_int), canonical_key(as_str))

    def test_pipe_in_fields_does_not_cause_collision(self):
        a = canonical_key(
            {"benchmark_name": "a|b", "conference": "c", "year": 2025}
        )
        b = canonical_key(
            {"benchmark_name": "a", "conference": "b|c", "year": 2025}
        )
        self.assertNotEqual(a, b)

    def test_backslash_in_fields_does_not_create_collision(self):
        a = canonical_key(
            {"benchmark_name": "a\\", "conference": "|b", "year": 2025}
        )
        b = canonical_key(
            {"benchmark_name": "a", "conference": "\\|b", "year": 2025}
        )
        self.assertNotEqual(a, b)

    def test_different_years_produce_different_keys(self):
        base = {"benchmark_name": "x", "conference": "y"}
        self.assertNotEqual(
            canonical_key({**base, "year": 2024}),
            canonical_key({**base, "year": 2025}),
        )
