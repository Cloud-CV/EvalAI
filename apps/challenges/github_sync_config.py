"""
Configuration for bi-directional GitHub sync.
Defines which Challenge and ChallengePhase fields should be synced to GitHub.
"""

# Challenge fields that should be synced to GitHub
CHALLENGE_SYNC_FIELDS = {
    "title",
    "short_description",
    "description",
    "terms_and_conditions",
    "submission_guidelines",
    "evaluation_details",
    "start_date",
    "end_date",
    "evaluation_script",
}

# ChallengePhase fields that should be synced to GitHub
CHALLENGE_PHASE_SYNC_FIELDS = {
    "name",
    "description",
    "start_date",
    "end_date",
    "max_submissions_per_day",
    "max_submissions_per_month",
    "max_submissions",
    "is_public",
    "is_submission_public",
    "test_annotation",
}

# Fields that are file-based (content stored in separate files)
CHALLENGE_FILE_FIELDS = {"evaluation_script"}

CHALLENGE_PHASE_FILE_FIELDS = {"test_annotation"}
