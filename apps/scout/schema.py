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
