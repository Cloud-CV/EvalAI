# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-02-03 15:27
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0004_submission_output'),
        ('challenges', '0018_added_challenge_phase_split_table'),
    ]

    operations = [
        migrations.CreateModel(
            name='LeaderboardData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('result', django.contrib.postgres.fields.jsonb.JSONField()),
                ('challenge_phase_split', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='challenges.ChallengePhaseSplit')),
                ('leaderboard', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='challenges.Leaderboard')),
                ('submission', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='jobs.Submission')),
            ],
            options={
                'db_table': 'leaderboard_data',
            },
        ),
    ]
