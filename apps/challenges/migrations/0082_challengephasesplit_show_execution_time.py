# Generated by Django 2.2.13 on 2021-03-15 08:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("challenges", "0081_add_efs_mount_meta_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="challengephasesplit",
            name="show_execution_time",
            field=models.BooleanField(default=False),
        ),
    ]
