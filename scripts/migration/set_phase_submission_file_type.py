# To run the file:
# 1. Open django shell using -- python manage.py shell
# 2. Run the script in shell -- exec(open('scripts/migration/set_phase_submission_file_type.py').read())

from challenges.models import ChallengePhase


def set_phase_submission_file_type():
    challengePhases = ChallengePhase.objects.all()
    try:
        for phase in challengePhases:
            print("Setting challengePhase file type default")
            phase.submission_file_type = (
                ".json, .zip, .txt, .tsv, .gz, .csv, .h5, .npy"
            )
            phase.save()
            print("Inserted default file type")
    except Exception as e:
        print(e)


set_phase_submission_file_type()
