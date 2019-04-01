# Command to run: python manage.py shell < scripts/migration/set_phase_slug_as_unique.py


def set_phase_slug_as_unique():
    from challenges.models import ChallengePhase

    challenge_phases = ChallengePhase.objects.all()
    try:
        for challenge_phase in challenge_phases:
            phase_slug = "{}-{}-{}".format(
                challenge_phase.challenge.title.split(" ")[0].lower(),
                challenge_phase.codename.replace(" ", "-").lower(),
                challenge_phase.challenge.pk,
            )
            print(
                "Adding Challenge Phase Slug: `%s` --> `%s` "
                % (challenge_phase.name, phase_slug)
            )
            challenge_phase.slug = phase_slug
            challenge_phase.save()
            print("Successfully added challenge phase slug")
    except Exception as e:
        print(e)


set_phase_slug_as_unique()
