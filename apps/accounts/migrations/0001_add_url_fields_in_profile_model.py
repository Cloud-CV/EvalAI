# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-07-29 17:59
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', 'remove_affiliation_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='github_url',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='google_scholar_url',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='linkedin_url',
            field=models.URLField(blank=True, null=True),
        ),
    ]
