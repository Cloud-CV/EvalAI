# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('authtoken', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExpiringToken',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('authtoken.token',),
        ),
    ]
