# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2018-06-29 03:34
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("jobs", "0008_remove_indexing_submission")]

    operations = [
        migrations.AlterField(
            model_name="submission",
            name="method_description",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AlterField(
            model_name="submission",
            name="method_name",
            field=models.CharField(db_index=True, default="", max_length=1000),
        ),
        migrations.AlterField(
            model_name="submission",
            name="project_url",
            field=models.CharField(default="", max_length=1000),
        ),
        migrations.AlterField(
            model_name="submission",
            name="publication_url",
            field=models.CharField(default="", max_length=1000),
        ),
    ]
