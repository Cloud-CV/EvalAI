from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("jobs", "0026_auto_20230804_1946"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="submission",
            index=models.Index(
                fields=["challenge_phase", "participant_team", "status"],
                name="sub_phase_team_status_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="submission",
            index=models.Index(
                fields=["challenge_phase", "participant_team", "submitted_at"],
                name="sub_phase_team_date_idx",
            ),
        ),
    ]
