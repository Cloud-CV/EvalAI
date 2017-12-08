## Migrations

> Migrations are Django’s way of propagating changes you make to your models (adding a field, deleting a model, etc.) into your database schema. They’re designed to be mostly automatic, but you’ll need to know when to make migrations, when to run them, and the common problems you might run into.
    - Django Migration [Docs](https://docs.djangoproject.com/en/1.10/topics/migrations/#module-django.db.migrations)


### Creating a migration

* We prefer that you create migrations for a single app and the change should be concerned with a single issue or feature.

```
# migration only for jobs app
python manage.py makemigrations jobs
```

* Always create named migrations. You can name migrations by passing `-n` or `--name` argument

```
python manage.py makemigrations jobs -n=execution_time_limit
# or
python manage.py makemigrations jobs --name=execution_time_limit
```

* While creating migrations on local environment don't forget to add development settings.

```
python manage.py makemigrations --settings=settings.dev
```

So a complete named migration for jobs app where in a execution time limit field is added to `Submission` model, will look like

```
python manage.py makemigrations jobs --name=execution_time_limit --settings=settings.dev
```

* Files created after running `makemigrations` should be committed along with other files

* While creating a migration for your concerned change, it may happen that some other changes are also there in the migration file. For example, adding a `execution_time_limit` field on `Submission` model also brings in the change for `when_made_public` being added. In that case, open an [new issue](https://github.com/Cloud-CV/EvalAI/issues/new) and clearly mention the issue over there. If possible, fix the issue yourself, by opening a new branch and creating migrations only for the concerned part. The idea here is that a commit should only include its concerned migration changes and nothing else.
