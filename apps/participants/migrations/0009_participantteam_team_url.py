# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2018-06-29 04:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('participants', '0008_added_unique_in_team_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='participantteam',
            name='team_url',
            field=models.CharField(default='', max_length=1000, null=True),
        ),
    ]
