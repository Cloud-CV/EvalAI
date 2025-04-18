# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-11-28 04:11
from __future__ import unicode_literals

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="ChallengeHost",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("Accepted", "Accepted"),
                            ("Denied", "Denied"),
                            ("Pending", "Pending"),
                            ("Self", "Self"),
                            ("Unknown", "Unknown"),
                        ],
                        max_length=30,
                    ),
                ),
                (
                    "permissions",
                    models.CharField(
                        choices=[
                            ("Admin", "Admin"),
                            ("Read", "Read"),
                            ("Restricted", "Restricted"),
                            ("Write", "Write"),
                        ],
                        max_length=30,
                    ),
                ),
            ],
            options={"db_table": "challenge_host"},
        ),
        migrations.CreateModel(
            name="ChallengeHostTeam",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                ("team_name", models.CharField(max_length=100)),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="challenge_host_team_creator",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"db_table": "challenge_host_teams"},
        ),
        migrations.AddField(
            model_name="challengehost",
            name="team_name",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="hosts.ChallengeHostTeam",
            ),
        ),
        migrations.AddField(
            model_name="challengehost",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
