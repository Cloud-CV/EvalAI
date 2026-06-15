from unittest import TestCase

import jsonschema
from scout.schema import OUTPUT_SCHEMA, validate_output_schema

VALID_PAYLOAD = {
    "challenges": [
        {
            "benchmark_name": "ImageNet-21K-P",
            "task_area": "vision",
            "conference": "NeurIPS",
            "year": 2025,
            "official_url": "https://imagenet21k.org/challenge",
            "dataset_url": "https://imagenet21k.org/data",
            "organizers": [
                {
                    "name": "Dr. Jane Doe",
                    "role": "PI",
                    "email": "jane@example.edu",
                    "affiliation": "Example University",
                }
            ],
            "evalai_suitable": True,
            "evalai_reasoning": "Standardized leaderboard hosting would help.",
        }
    ]
}


class OutputSchemaTests(TestCase):
    def test_valid_payload_passes(self):
        validate_output_schema(VALID_PAYLOAD)

    def test_missing_required_top_level_key_fails(self):
        with self.assertRaises(jsonschema.ValidationError):
            validate_output_schema({})

    def test_challenge_missing_required_field_fails(self):
        bad = {
            "challenges": [
                {
                    "task_area": "vision",
                    "conference": "NeurIPS",
                    "year": 2025,
                    "official_url": "https://x",
                    "organizers": [{"name": "x"}],
                    "evalai_suitable": True,
                    "evalai_reasoning": "x",
                }
            ]
        }
        with self.assertRaises(jsonschema.ValidationError):
            validate_output_schema(bad)

    def test_organizer_only_requires_name(self):
        partial = {
            "challenges": [
                {
                    "benchmark_name": "x",
                    "task_area": "vision",
                    "conference": "NeurIPS",
                    "year": 2025,
                    "official_url": "https://x",
                    "organizers": [{"name": "only-name"}],
                    "evalai_suitable": False,
                    "evalai_reasoning": "x",
                }
            ]
        }
        validate_output_schema(partial)

    def test_invalid_official_url_fails(self):
        bad = {
            "challenges": [
                {
                    **VALID_PAYLOAD["challenges"][0],
                    "official_url": "not-a-uri",
                }
            ]
        }
        with self.assertRaises(jsonschema.ValidationError):
            validate_output_schema(bad)

    def test_invalid_dataset_url_fails(self):
        bad = {
            "challenges": [
                {
                    **VALID_PAYLOAD["challenges"][0],
                    "dataset_url": "ftp://bad.example/data",
                }
            ]
        }
        with self.assertRaises(jsonschema.ValidationError):
            validate_output_schema(bad)

    def test_output_schema_still_declares_uri_format(self):
        self.assertEqual(
            OUTPUT_SCHEMA["properties"]["challenges"]["items"]["properties"][
                "official_url"
            ]["format"],
            "uri",
        )
