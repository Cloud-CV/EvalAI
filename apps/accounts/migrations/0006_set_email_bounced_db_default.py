from django.db import migrations


class Migration(migrations.Migration):
    """Set a persistent database-level DEFAULT on email_bounced.

    Django's AddField drops the DB default after backfilling existing rows,
    leaving the column with NOT NULL but no default. During rolling deploys,
    old application code that doesn't know about the column will omit it from
    INSERT statements, causing IntegrityError.
    """

    dependencies = [
        ("accounts", "0005_add_unique_email_constraint"),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "ALTER TABLE user_profile "
                "ALTER COLUMN email_bounced "
                "SET DEFAULT false;"
            ),
            reverse_sql=(
                "ALTER TABLE user_profile "
                "ALTER COLUMN email_bounced "
                "DROP DEFAULT;"
            ),
        ),
    ]
