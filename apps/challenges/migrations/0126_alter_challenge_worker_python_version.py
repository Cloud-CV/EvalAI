from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("challenges", "0125_challenge_worker_python_version"),
    ]

    operations = [
        migrations.AlterField(
            model_name="challenge",
            name="worker_python_version",
            field=models.CharField(
                blank=True,
                default="3.9",
                help_text="Python version for the Fargate submission worker image (3.7, 3.8, 3.9).",
                max_length=10,
                null=True,
            ),
        ),
    ]
