from base.utils import get_model_object

from .models import Challenge, ChallengePhase


get_challenge_model = get_model_object(Challenge)

get_challenge_phase_model = get_model_object(ChallengePhase)
