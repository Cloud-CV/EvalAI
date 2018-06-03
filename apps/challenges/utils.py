import os

from base.utils import get_model_object

from .models import Challenge, ChallengePhase, Leaderboard, DatasetSplit, ChallengePhaseSplit


get_challenge_model = get_model_object(Challenge)

get_challenge_phase_model = get_model_object(ChallengePhase)

get_leaderboard_model = get_model_object(Leaderboard)

get_dataset_split_model = get_model_object(DatasetSplit)

get_challenge_phase_split_model = get_model_object(ChallengePhaseSplit)


def get_file_content(file_path, mode):
    if os.path.isfile(file_path):
        with open(file_path, mode) as file_content:
            return file_content.read()


def get_challenge_phase_from_phase_id(challenge, challenge_phase_id):
    try:
        challenge_phase_obj = ChallengePhase.objects.get(challenge=challenge, phase_id=challenge_phase_id)
    except ChallengePhase.DoesNotExist:
        return None
    return challenge_phase_obj
