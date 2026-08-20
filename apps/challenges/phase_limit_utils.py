from django.conf import settings
from django.db.models import Count

from .models import ChallengePhase


CHALLENGE_PHASE_LIMIT_CONTACT_MESSAGE = (
    "This challenge is limited to {limit} phase(s). Contact us at "
    "team@eval.ai if you need more phases."
)


def get_challenge_phase_limit(challenge):
    """
    Return the phase cap for a challenge, or None when unlimited.
    """
    if challenge is None:
        return settings.DEFAULT_MAX_CHALLENGE_PHASES
    if challenge.max_allowed_phases is None:
        return None
    return challenge.max_allowed_phases


def get_challenge_phase_count(challenge):
    annotated_count = getattr(challenge, "_phase_count", None)
    if annotated_count is not None:
        return annotated_count
    return ChallengePhase.objects.filter(challenge=challenge).count()


def with_challenge_phase_count(queryset):
    return queryset.annotate(_phase_count=Count("challengephase"))


def get_challenge_phase_limit_error(challenge, proposed_phase_count):
    phase_limit = get_challenge_phase_limit(challenge)
    if phase_limit is None:
        return None
    if proposed_phase_count > phase_limit:
        return CHALLENGE_PHASE_LIMIT_CONTACT_MESSAGE.format(limit=phase_limit)
    return None
