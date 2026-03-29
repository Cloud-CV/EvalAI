from django.conf import settings
from django.db import migrations


def remove_duplicate_star_challenges(apps, schema_editor):
    """
    For each (user, challenge) pair that has more than one StarChallenge row,
    keep the first one (lowest pk) and delete the rest.
    """
    StarChallenge = apps.get_model("challenges", "StarChallenge")
    from django.db.models import Count, Min

    duplicates = (
        StarChallenge.objects.values("user", "challenge")
        .annotate(cnt=Count("id"), min_id=Min("id"))
        .filter(cnt__gt=1)
    )
    for dup in duplicates:
        StarChallenge.objects.filter(
            user=dup["user"], challenge=dup["challenge"]
        ).exclude(pk=dup["min_id"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        (
            "challenges",
            "0119_add_is_submission_paused_to_challenge_and_phase",
        ),
    ]

    operations = [
        migrations.RunPython(
            remove_duplicate_star_challenges,
            migrations.RunPython.noop,
        ),
        migrations.AlterUniqueTogether(
            name="starchallenge",
            unique_together={("user", "challenge")},
        ),
    ]
