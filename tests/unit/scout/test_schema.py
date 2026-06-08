from unittest import TestCase

import jsonschema
from scout.schema import OUTPUT_SCHEMA

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
        jsonschema.validate(VALID_PAYLOAD, OUTPUT_SCHEMA)

    def test_missing_required_top_level_key_fails(self):
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate({}, OUTPUT_SCHEMA)

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
            jsonschema.validate(bad, OUTPUT_SCHEMA)

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
        jsonschema.validate(partial, OUTPUT_SCHEMA)
