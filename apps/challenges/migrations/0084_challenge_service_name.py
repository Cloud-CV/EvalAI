# Generated by Django 2.2.13 on 2021-04-05 16:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('challenges', '0083_challengephase_annotations_uploaded_using_cli'),
    ]

    operations = [
        migrations.AddField(
            model_name='challenge',
            name='service_name',
            field=models.CharField(blank=True, default='', max_length=2048, null=True),
        ),
    ]
