import traceback

from challenges.models import ChallengePhase

challenge_phases = ChallengePhase.objects.all()

try:
    for phase in challenge_phases:
        phase.max_submissions_per_month = phase.max_submissions
        phase.save()
except Exception as e:
    print(e)
    print(traceback.print_exc())
