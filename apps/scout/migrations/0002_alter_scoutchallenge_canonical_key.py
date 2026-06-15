from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("scout", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="scoutchallenge",
            name="canonical_key",
            field=models.CharField(db_index=True, max_length=64, unique=True),
        ),
    ]
