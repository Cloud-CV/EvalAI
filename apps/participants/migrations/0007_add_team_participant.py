# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-12-03 04:58
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('participants', '0006_alter_status_participant_choices'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='participantteammember',
            name='participant',
        ),
        migrations.RemoveField(
            model_name='participantteammember',
            name='team',
        ),
        migrations.AddField(
            model_name='participant',
            name='team',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='participants', to='participants.ParticipantTeam'),
        ),
        migrations.DeleteModel(
            name='ParticipantTeamMember',
        ),
    ]
