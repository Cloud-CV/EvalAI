# Generated by Django 2.2.13 on 2021-06-11 14:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("jobs", "0020_submission_submission_input_file"),
    ]

    operations = [
        migrations.AddField(
            model_name="submission",
            name="is_verified_by_host",
            field=models.BooleanField(default=False),
        ),
    ]
