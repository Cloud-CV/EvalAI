# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-07-05 15:00
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("web", "0007_add_position_in_team_model")]

    operations = [
        migrations.AlterField(
            model_name="team",
            name="description",
            field=models.TextField(blank=True, null=True),
        )
    ]
