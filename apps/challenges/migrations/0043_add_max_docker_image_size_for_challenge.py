# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2019-02-14 19:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('challenges', '0042_add_slug_field_and_flag_for_docker_based_challenges'),
    ]

    operations = [
        migrations.AddField(
            model_name='challenge',
            name='max_docker_image_size',
            field=models.PositiveIntegerField(blank=True, default=50, null=True),
        ),
    ]
