# Generated by Django 2.2.20 on 2023-07-31 22:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('challenges', '0098_challenge_tags_domains'),
    ]

    operations = [
        migrations.AddField(
            model_name='challenge',
            name='worker_image_url',
            field=models.URLField(blank=True, default=None, null=True),
        ),
    ]
