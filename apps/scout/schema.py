from urllib.parse import urlparse

import jsonschema

OUTPUT_SCHEMA = {
    "type": "object",
    "required": ["challenges"],
    "properties": {
        "challenges": {
            "type": "array",
            "items": {
                "type": "object",
                "required": [
                    "benchmark_name",
                    "task_area",
                    "conference",
                    "year",
                    "official_url",
                    "organizers",
                    "evalai_suitable",
                    "evalai_reasoning",
                ],
                "properties": {
                    "benchmark_name": {"type": "string"},
                    "task_area": {
                        "type": "string",
                        "description": (
                            "vision | NLP | multimodal | RL | robustness | "
                            "medical imaging | speech | other"
                        ),
                    },
                    "conference": {
                        "type": "string",
                        "description": (
                            "CVPR | NeurIPS | ICCV | ECCV | ICLR | AAAI | "
                            "IJCAI | EMNLP | ACL | other"
                        ),
                    },
                    "year": {"type": "integer"},
                    "official_url": {"type": "string", "format": "uri"},
                    "dataset_url": {
                        "type": "string",
                        "description": (
                            "Dataset page or official repo. "
                            "Empty string if none."
                        ),
                    },
                    "organizers": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["name"],
                            "properties": {
                                "name": {"type": "string"},
                                "role": {"type": "string"},
                                "email": {
                                    "type": "string",
                                    "description": (
                                        "Official public email only. "
                                        "Empty string if not found."
                                    ),
                                },
                                "affiliation": {"type": "string"},
                            },
                        },
                    },
                    "evalai_suitable": {"type": "boolean"},
                    "evalai_reasoning": {
                        "type": "string",
                        "description": "1-2 lines",
                    },
                },
            },
        }
    },
}


def _is_valid_http_url(value):
    if not isinstance(value, str) or not value:
        return False
    parsed = urlparse(value)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def validate_output_schema(payload):
    """Validate a Yutori scout payload against OUTPUT_SCHEMA.

    jsonschema 3.x does not enforce ``format: uri`` without a custom
    FormatChecker (and upgrading jsonschema does not fix that). We keep
    ``format: uri`` in the schema as documentation for Yutori and apply
    explicit http(s) URL checks here instead of bumping the dependency.
    """
    jsonschema.validate(payload, OUTPUT_SCHEMA)
    for idx, challenge in enumerate(payload.get("challenges", [])):
        official_url = challenge.get("official_url")
        if not _is_valid_http_url(official_url):
            raise jsonschema.ValidationError(
                "Invalid official_url for challenges[{}]: {!r}".format(
                    idx, official_url
                )
            )
        dataset_url = challenge.get("dataset_url", "")
        if dataset_url and not _is_valid_http_url(dataset_url):
            raise jsonschema.ValidationError(
                "Invalid dataset_url for challenges[{}]: {!r}".format(
                    idx, dataset_url
                )
            )
