# Fields from Challenge, ChallengePhase model to be considered for github_sync

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
]

challenge_file_fields = [
    "description",
    "evaluation_details",
    "terms_and_conditions",
    "submission_guidelines",
]

challenge_phase_non_file_fields = [
    "name",
    "leaderboard_public",
    "is_public",
    "is_submission_public",
    "start_date",
    "end_date",
    "max_submissions_per_day",
    "max_submissions_per_month",
    "max_submissions",
    "is_restricted_to_select_one_submission",
    "is_partial_submission_evaluation_enabled",
    "allowed_submission_file_types",
]

challenge_phase_file_fields = ["description"]