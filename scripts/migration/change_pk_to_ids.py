# Command to run: python manage.py shell < scripts/migration/change_pk_to_ids.py

from challenges.models import Challenge, ChallengePhase, ChallengePhaseSplit


def change_pk_to_ids():

    challenges = Challenge.objects.all()
    for challenge in challenges:
        phases = ChallengePhase.objects.filter(challenge=challenge).order_by("pk")
        phase_idx = 1
        challenge_phase_split_idx = 1
        for phase in phases:
            phase.phase_id = phase_idx
            phase.save()
            print "{}, {} PK changed to {}".format(challenge.title, phase.name, phase_idx)
            phase_idx += 1
            phase_splits =  ChallengePhaseSplit.objects.filter(challenge_phase=phase).order_by("pk")
            for phase_split in phase_splits:
                phase_split.phase_split_id = challenge_phase_split_idx
                phase_split.challenge = challenge
                phase_split.save()
                print "{}, Split {}'s PK changed to {}".format(phase.name, phase_split.pk, challenge_phase_split_idx)
                challenge_phase_split_idx += 1

change_pk_to_ids()
