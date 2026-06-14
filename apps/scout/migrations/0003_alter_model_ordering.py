from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("scout", "0002_alter_scoutchallenge_canonical_key"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="scoutrun",
            options={"ordering": ("-received_at",)},
        ),
        migrations.AlterModelOptions(
            name="scoutchallenge",
            options={"ordering": ("-first_seen",)},
        ),
    ]
