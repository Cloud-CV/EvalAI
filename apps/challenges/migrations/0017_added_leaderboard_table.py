# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-02-03 14:32
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("challenges", "0016_added_dataset_split_as_m2m_field")]

    operations = [
        migrations.CreateModel(
            name="Leaderboard",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                ("schema", django.contrib.postgres.fields.jsonb.JSONField()),
            ],
            options={"db_table": "leaderboard"},
        )
    ]
