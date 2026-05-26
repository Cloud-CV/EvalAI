from django.db import migrations, models


def migrate_other_challenge_usage_type_to_paid(apps, schema_editor):
    Challenge = apps.get_model("challenges", "Challenge")
    Challenge.objects.filter(challenge_usage_type="other").update(
        challenge_usage_type="paid"
    )


class Migration(migrations.Migration):

    dependencies = [
        ("challenges", "0122_add_challenge_usage_and_retention_policy"),
    ]

    operations = [
        migrations.RunPython(
            migrate_other_challenge_usage_type_to_paid,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="challenge",
            name="challenge_usage_type",
            field=models.CharField(
                choices=[
                    ("paid", "Paid"),
                    ("internal", "Internal"),
                ],
                db_index=True,
                default="paid",
                max_length=20,
            ),
        ),
    ]
