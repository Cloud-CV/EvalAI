## Frequently Asked Questions

#### Q. How to start contributing?

EvalAI’s issue tracker is good place to start. If you find something that interests you, comment on the thread and we’ll help get you started.
Alternatively, if you come across a new bug on the site, please file a new issue and comment if you would like to be assigned. Existing issues are tagged with one or more labels, based on the part of the website it touches, its importance etc., which can help you select one.

#### Q. What are the technologies that EvalAI uses?

Please refer to [Technologies Used](https://evalai.readthedocs.io/en/latest/architecture.html)

#### Q. Where could I learn GitHub Commands?

Refer to [GitHub Guide](https://help.github.com/articles/git-and-github-learning-resources/).

#### Q. Where could I learn Markdown?

Refer to [Markdown Guide](https://guides.github.com/features/mastering-markdown/).

#### Q. What to do when coverage decreases in your pull request?

Coverage decreases when the existing test cases don't test the new code you wrote. If you click coverage, you can see exactly which all parts aren't covered and you can write new tests to test the parts.

### Common Errors during installation

#### Q. While using `pip install -r dev/requirement.txt`

```
  Writing manifest file 'pip-egg-info/psycopg2.egg-info/SOURCES.txt'
  Error: You need to install postgresql-server-dev-X.Y for building a server-side extension or
  libpq-dev for building a client-side application.
  ----------------------------------------
  Command "python setup.py egg_info" failed with error code 1 in /tmp/pip-build-qIjU8G/psycopg2/
```

Use the following commands in order to solve the error:

1. `sudo apt-get install postgresql`
2. `sudo apt-get install python-psycopg2`
3. `sudo apt-get install libpq-dev`

#### Q. While using `pip install -r dev/requirement.txt`

```
Command “python setup.py egg_info” failed with error code 1 in
/private/var/folders/c7/b45s17816zn_b1dh3g7yzxrm0000gn/T/pip-build- GM2AG/psycopg2/
```

Firstly check that you have installed all the mentioned dependencies.
Then, Upgrade the version of postgresql to 10.1 in order to solve it.

#### Q. While using docker, I am getting the following error on URL [http://localhost:8888/](http://localhost:8888/):

```
Cannot Get \
```

Try removing the docker containers and then building them again.

#### Q. Getting the following error while executing command `createdb evalai -U postgres`:

```
createdb: could not connect to database template1: FATAL: Peer authentication failed for user "postgres"
```

Try creating a new user and then grant all the privileges to it and then create a db.

#### Q. While running the unit tests, I am getting the error similar to as shown below:

```
________________ ERROR collecting tests/unit/web/test_views.py _________________
import file mismatch:
imported module 'tests.unit.web.test_views' has this __file__ attribute:
  /path/to/evalai/tests/unit/web/test_views.py
which is not the same as the test file we want to collect:
  /code/tests/unit/web/test_views.py
HINT: remove __pycache__ / .pyc files and/or use a unique basename for your test file modules
```

It appears that you are trying to run `pytest` in a docker container. To fix this, delete the `__pycache__` and all `*.pyc` files using the following command:

`find . | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf`

#### Q. Getting the following error:

```
ERROR: for db Cannot start service db: driver failed programming external connectivity on endpoint evalai_db_1 (2163096de9aac6561b4f699bb1049acd0ce881fbaa0da28e47cfa9ca0ee1199f): Error starting userland proxy: listen tcp 0.0.0.0:5432: bind: address already in use
```

The following solution only works on Linux.

Execute :
`sudo netstat -lpn |grep :5432`

The output of the above would be in the following form:

```
tcp 0 0 127.0.0.1:5432 0.0.0.0:* LISTEN 25273/postgres
```

Execute the following command:

```
sudo kill 25273 ## This would vary and you can change with the output in the first step
```

#### Q. Getting the following error when using Docker:

```
ERROR : Version in "./docker-compose.yml" is unsupported. You might be seeing this error because you are using wrong Compose file version.
```

Since, the version of compose file is 3. You might be using a docker version which is not compatible. You can upgrade your docker engine and try again.

#### Q. Getting the following error while running `python manage.py runserver --settings=settings.dev`:

```
Starting the database seeder. Hang on...
Are you sure you want to wipe the existing development database and reseed it? (Y/N)
Exception while running run() in 'scripts.seed'
```

Try clearing the postgres database manually and try again.

#### Q. While trying to build EvalAI from the master branch and run the command docker-compose up:

```
ERROR: Service 'celery' failed to build: pull access denied for evalai_django, repository does not exist or may require 'docker login': denied: requested access to the resource is denied
```

Please make sure to clone EvalAI in its default directory with name evalai. This happens because the parent directory changes the name of docker images.
For instance, the image evalai_django gets renamed to evalai_dev_django if your directory is renamed to EvalAI_dev.
