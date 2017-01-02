# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-12-30 08:07
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('challenges', '0007_rename_test_environment'),
    ]

    operations = [
        migrations.AddField(
            model_name='challengephase',
            name='max_submissions',
            field=models.PositiveIntegerField(default=100000),
        ),
        migrations.AddField(
            model_name='challengephase',
            name='max_submissions_per_day',
            field=models.PositiveIntegerField(default=100000),
        ),
    ]
