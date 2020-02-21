# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2020-02-17 22:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_add_url_fields_in_profile_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='avatar_image',
            field=models.ImageField(default='/frontend/src/images/pro-pic.png', upload_to='test_folder'),
        ),
    ]
