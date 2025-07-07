from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("challenges", "0112_challenge_sqs_retention_period"),
    ]

    operations = [
        migrations.AddField(
            model_name="challenge",
            name="log_retention_days_override",
            field=models.PositiveIntegerField(
                null=True,
                blank=True,
                default=None,
                help_text="Override CloudWatch log retention period in days for this challenge.",
            ),
        ),
    ] 