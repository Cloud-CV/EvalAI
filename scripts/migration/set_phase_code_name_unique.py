# Command to run: python manage.py shell < scripts/migration/set_phase_code_name_unique.py

from challenges.models import ChallengePhase


def set_phase_code_name_unique():

    challenge_phases = ChallengePhase.objects.all()
    try:
        for challenge_phase in challenge_phases:
            new_phase_code_name = "{0}_{1}".format(
                challenge_phase.code_name, challenge_phase.id
            )
            print(
                "Modifying Challenge Phase Code Name: `%s` --> `%s` "
                % (challenge_phase.code_name, new_phase_code_name)
            )
            challenge_phase.code_name = new_phase_code_name
            challenge_phase.save()
            print("Successfully modified Challenge Phase Code Name")
    except Exception as e:
        print(e)


set_phase_code_name_unique()
