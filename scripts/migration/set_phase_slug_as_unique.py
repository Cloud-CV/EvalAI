# To run the file:
# 1. Open django shell using -- python manage.py shell
# 2. Run the script in shell -- exec(open('scripts/migration/set_phase_slug_as_unique.py').read())

from challenges.models import ChallengePhase


def set_phase_slug_as_unique():
    challenge_phases = ChallengePhase.objects.all()
    try:
        for challenge_phase in challenge_phases:
            phase_slug = "{}-{}-{}".format(
                challenge_phase.challenge.title.split(" ")[0].lower(),
                challenge_phase.codename.replace(" ", "-").lower(),
                challenge_phase.challenge.pk,
            )
            print(
                "Adding challenge phase slug: `%s` --> `%s` "
                % (challenge_phase.name, phase_slug)
            )
            challenge_phase.slug = phase_slug
            challenge_phase.save()
            print("Successfully added challenge phase slug")
    except Exception as e:
        print(e)


set_phase_slug_as_unique()
