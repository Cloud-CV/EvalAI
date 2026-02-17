"""
Queryset utility functions for challenges app
"""

from jobs.models import Submission


def get_submissions_queryset(challenge_phase, participant_team=None):
    """
    Get optimized submissions queryset with select_related and prefetch_related
    to avoid N+1 query issues

    Args:
        challenge_phase: ChallengePhase instance
        participant_team: ParticipantTeam instance (optional, for filtering by team)

    Returns:
        QuerySet: Optimized submissions queryset with related data prefetched
    """
    queryset = (
        Submission.objects.filter(challenge_phase=challenge_phase)
        .select_related("participant_team", "challenge_phase", "created_by")
        .prefetch_related("participant_team__participants__user__profile")
    )

    if participant_team:
        queryset = queryset.filter(participant_team=participant_team)
    else:
        queryset = queryset.filter(ignore_submission=False)

    return queryset.order_by("-submitted_at")
