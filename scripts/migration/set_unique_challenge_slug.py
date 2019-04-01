# To run the file:
# 1. Open django shell using -- python manage.py shell
# 2. Run the script in shell -- exec(open('scripts/migration/set_unique_challenge_slug.py').read())

from challenges.models import Challenge


def set_challenge_slug_as_unique():
    challenges = Challenge.objects.all()
    try:
        for challenge in challenges:
            slug = "{}-{}".format(
                challenge.title.replace(" ", "-").lower(), challenge.pk
            )[:199]
            print(
                "Adding challenge slug: `%s` --> `%s` "
                % (challenge.title, slug)
            )
            challenge.slug = slug
            challenge.save()
            print("Successfully added challenge slug")
    except Exception as e:
        print(e)


set_challenge_slug_as_unique()
