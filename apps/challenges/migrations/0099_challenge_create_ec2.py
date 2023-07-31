# Generated by Django 2.2.20 on 2023-07-31 20:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('challenges', '0098_challenge_tags_domains'),
    ]

    operations = [
        migrations.AddField(
            model_name='challenge',
            name='create_ec2',
            field=models.BooleanField(db_index=True, default=False, verbose_name='Creates separate ec2 instance'),
        ),
    ]
