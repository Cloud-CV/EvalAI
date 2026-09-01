from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("challenges", "0130_add_challenge_field_help_text"),
    ]

    operations = [
        migrations.AddField(
            model_name="challengeevaluationcluster",
            name="nodegroup_name",
            field=models.CharField(blank=True, max_length=512, null=True),
        ),
    ]
