# -*- coding: utf-8 -*-
#Submitted by Anil Choudary

from __future__ import unicode_literals

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('challenges', '0074_add_default_meta_attributes_field.py'),
    ]

    operations = [
        migrations.AddField(
            model_name='challenge',
            name='tags',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.TextField(blank=True, null=True), blank=True, default=[], size=None),
        ),
    ]
