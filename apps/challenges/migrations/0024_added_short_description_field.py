# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-03-26 23:07
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('challenges', '0023_upload_unique_random_filename'),
    ]

    operations = [
        migrations.AddField(
            model_name='challenge',
            name='short_description',
            field=models.TextField(blank=True, null=True),
        ),
    ]
