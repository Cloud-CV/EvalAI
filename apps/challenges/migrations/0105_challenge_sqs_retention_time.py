# Generated by Django 2.2.20 on 2023-08-22 16:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('challenges', '0104_challenge_evaluation_module_error'),
    ]

    operations = [
        migrations.AddField(
            model_name='challenge',
            name='sqs_retention_time',
            field=models.IntegerField(default=259200),
        ),
    ]