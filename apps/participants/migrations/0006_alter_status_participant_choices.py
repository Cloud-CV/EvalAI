# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-12-03 04:48
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('participants', '0005_remove_participantteam_challenge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='participant',
            name='status',
            field=models.CharField(choices=[('Accepted', 'Accepted'), ('Denied', 'Denied'), ('Pending', 'Pending'), ('Self', 'Self'), ('Unknown', 'Unknown')], max_length=30),
        ),
        migrations.DeleteModel(
            name='ParticipantStatus',
        ),
    ]
