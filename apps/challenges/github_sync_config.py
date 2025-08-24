# Fields from Challenge, ChallengePhase model to be considered for github_sync
# If you are not sure what all these fields mean, please refer our documentation here:
# https://evalai.readthedocs.io/en/latest/configuration.html

challenge_non_file_fields = [
    "title",
    "short_description", 
    "leaderboard_description",
    "remote_evaluation",
    "is_docker_based",
    "is_static_dataset_code_upload",
    "start_date",
    "end_date",
    "published",
    "image",
    "evaluation_script",
    "tags",
]

challenge_file_fields = [
    "description",
    "evaluation_details",
    "terms_and_conditions",
    "submission_guidelines",
]

challenge_phase_non_file_fields = [
    "id",
    "name",
    "leaderboard_public",
    "is_public",
    "challenge",
    "is_active",
    "max_concurrent_submissions_allowed",
    "allowed_email_ids",
    "disable_logs",
    "is_submission_public",
    "start_date",
    "end_date",
    "test_annotation_file",
    "codename",
    "max_submissions_per_day",
    "max_submissions_per_month",
    "max_submissions",
    "is_restricted_to_select_one_submission",
    "is_partial_submission_evaluation_enabled",
    "allowed_submission_file_types",
    "default_submission_meta_attributes",
    "submission_meta_attributes",
]

challenge_phase_file_fields = [
    "description",
]

# Additional sections that should be synced
challenge_additional_sections = [
    "leaderboard",
    "dataset_splits", 
    "challenge_phase_splits",
]