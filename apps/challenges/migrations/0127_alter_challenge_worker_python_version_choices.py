from django.db import migrations, models


def backfill_worker_python_version(apps, schema_editor):
    Challenge = apps.get_model("challenges", "Challenge")
    Challenge.objects.filter(worker_python_version__isnull=True).update(
        worker_python_version="3.9"
    )
    Challenge.objects.filter(worker_python_version="").update(
        worker_python_version="3.9"
    )


class Migration(migrations.Migration):

    dependencies = [
        ("challenges", "0126_alter_challenge_worker_python_version"),
    ]

    operations = [
        migrations.RunPython(
            backfill_worker_python_version,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="challenge",
            name="worker_python_version",
            field=models.CharField(
                blank=True,
                choices=[("3.7", "3.7"), ("3.8", "3.8"), ("3.9", "3.9")],
                default="3.9",
                help_text=(
                    "Python version for the Fargate submission worker image "
                    "(3.7, 3.8, 3.9)."
                ),
                max_length=10,
            ),
        ),
    ]
