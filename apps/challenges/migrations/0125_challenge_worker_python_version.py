from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("challenges", "0124_challenge_max_team_members"),
    ]

    operations = [
        migrations.AddField(
            model_name="challenge",
            name="worker_python_version",
            field=models.CharField(
                blank=True,
                default="3.9",
                help_text="Python version for the Fargate submission worker image (3.7, 3.8, or 3.9).",
                max_length=10,
                null=True,
            ),
        ),
    ]
