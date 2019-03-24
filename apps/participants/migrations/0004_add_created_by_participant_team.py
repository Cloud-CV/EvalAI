# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-12-02 14:17
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("participants", "0003_remove_participant_challenge"),
    ]

    operations = [
        migrations.AddField(
            model_name="participantteam",
            name="created_by",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
        )
    ]
