# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-06-20 07:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('challenges', '0053_added_is_registration_open_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='challenge',
            name='task_def_arn',
            field=models.CharField(default='', max_length=2048),
        ),
        migrations.AddField(
            model_name='challenge',
            name='workers',
            field=models.IntegerField(blank=True, default=None, null=True),
        ),
    ]
