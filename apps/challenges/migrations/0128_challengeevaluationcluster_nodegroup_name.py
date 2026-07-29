from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("challenges", "0127_alter_challenge_worker_python_version_choices"),
    ]

    operations = [
        migrations.AddField(
            model_name="challengeevaluationcluster",
            name="nodegroup_name",
            field=models.CharField(blank=True, max_length=512, null=True),
        ),
    ]
