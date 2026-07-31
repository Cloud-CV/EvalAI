# Generated manually for use_fifo_sqs help_text update

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("challenges", "0133_alter_challenge_min_ecs_workers_default"),
    ]

    operations = [
        migrations.AlterField(
            model_name="challenge",
            name="use_fifo_sqs",
            field=models.BooleanField(
                default=False,
                help_text=(
                    "Use a FIFO SQS queue for ordered per-team evaluation "
                    "within a phase. Message groups are "
                    "phase_pk-participant_team_pk so different teams can be "
                    "processed in parallel by ECS workers. Do not toggle "
                    "after queue creation; provision a new challenge "
                    "instead."
                ),
            ),
        ),
    ]
