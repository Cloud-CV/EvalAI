# Generated by Django 2.2.13 on 2021-05-28 12:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("challenges", "0083_challengephase_annotations_uploaded_using_cli"),
    ]

    operations = [
        migrations.AddField(
            model_name="challenge",
            name="is_static_dataset_docker_based_challenge",
            field=models.BooleanField(
                db_index=True,
                default=False,
                verbose_name="Is static dataset docker based",
            ),
        ),
    ]
