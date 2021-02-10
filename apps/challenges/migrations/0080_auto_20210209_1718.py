# Generated by Django 2.2.13 on 2021-02-09 17:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('challenges', '0079_add_code_upload_setup_vpc_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='challengeevaluationcluster',
            name='ecr_all_access_policy_name',
            field=models.CharField(blank=True, max_length=512, null=True),
        ),
        migrations.AddField(
            model_name='challengeevaluationcluster',
            name='eks_role_name',
            field=models.CharField(blank=True, max_length=512, null=True),
        ),
        migrations.AddField(
            model_name='challengeevaluationcluster',
            name='node_group_role_name',
            field=models.CharField(blank=True, max_length=512, null=True),
        ),
        migrations.AddField(
            model_name='challengeevaluationcluster',
            name='nodegroup_name',
            field=models.CharField(blank=True, max_length=512, null=True),
        ),
    ]
