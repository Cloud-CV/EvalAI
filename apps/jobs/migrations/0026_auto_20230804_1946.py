# Generated by Django 2.2.20 on 2023-08-04 19:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("jobs", "0025_submission_rerun_resumed_at"),
    ]

    operations = [
        migrations.AlterField(
            model_name="submission",
            name="status",
            field=models.CharField(
                choices=[
                    ("submitted", "submitted"),
                    ("running", "running"),
                    ("failed", "failed"),
                    ("cancelled", "cancelled"),
                    ("resuming", "resuming"),
                    ("queued", "queued"),
                    ("finished", "finished"),
                    ("submitting", "submitting"),
                    ("archived", "archived"),
                    ("partially_evaluated", "partially_evaluated"),
                ],
                db_index=True,
                max_length=30,
            ),
        ),
    ]
