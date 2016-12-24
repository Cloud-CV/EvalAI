# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-12-24 09:23
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('challenges', '0004_challenge_is_disabled'),
    ]

    operations = [
        migrations.CreateModel(
            name='TestEnvironment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('leaderboard_public', models.BooleanField(default=False)),
                ('start_date', models.DateTimeField(blank=True, null=True, verbose_name='Start Date (UTC)')),
                ('end_date', models.DateTimeField(blank=True, null=True, verbose_name='End Date (UTC)')),
                ('test_annotation', models.FileField(upload_to=b'')),
            ],
            options={
                'db_table': 'challenge_test_env',
            },
        ),
        migrations.RemoveField(
            model_name='phase',
            name='challenge',
        ),
        migrations.AddField(
            model_name='challenge',
            name='evaluation_script',
            field=models.FileField(default=False, upload_to=b''),
        ),
        migrations.DeleteModel(
            name='Phase',
        ),
        migrations.AddField(
            model_name='testenvironment',
            name='challenge',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='challenges.Challenge'),
        ),
    ]
