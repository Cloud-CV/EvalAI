## Frequently Asked Questions

#### Q. How to start contributing?

EvalAI’s issue tracker is good place to start. If you find something that interests you, comment on the thread and we’ll help get you started.
Alternatively, if you come across a new bug on the site, please file a new issue and comment if you would like to be assigned. Existing issues are tagged with one or more labels, based on the part of the website it touches, its importance etc., which can help you select one.

#### Q. What are the technologies that EvalAI uses?

##### Django

Django is the heart of the application, which powers our backend. We use Django version 1.11.18.

##### Django Rest Framework

We use Django Rest Framework for writing and providing REST APIs. It's permission and serializers have helped write a maintainable codebase.

##### AWS Simple Queue Service (SQS)

We currently use AWS SQS for queueing submission messages which are then later on processed by a Python worker.

##### PostgreSQL

PostgresSQL is used as our primary datastore. All our tables currently reside in a single database named evalai.

##### Angular JS - ^1.6.1

Angular JS is a well-known framework that powers our frontend.

#### Q. Where could I learn Github Commands?

Refer to [Github Guide](https://help.github.com/articles/git-and-github-learning-resources/).

#### Q. Where could I learn Markdown?

Refer to [MarkDown Guide](https://guides.github.com/features/mastering-markdown/).

#### Q. What to do when coverage decreases in your pull request?

Coverage decreases when the existing test cases don't test the new code you wrote. If you click coverage, you can see exactly which all parts aren't covered and you can write new tests to test the parts.

#### Q. How to setup EvalAI using virtualenv?
We have removed the documentation for setting up using virtual environment since the project has grown and different developers face different dependency issues. We recommend to setup EvalAI using docker based environment.

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

#### Q. Getting an import error

```
Couldn't import Django,"when using command python manage.py migrate
```

Firstly, check that you have activated the virtualenv.
Install python dependencies using the following commands on the command line

```
cd evalai
pip install -r requirements/dev.txt
```

#### Q. Getting Mocha Error

```
Can not load reporter “mocha”,it is not registered
```

Uninstall karma and then install

```
npm uninstall -g generator-karma && npm install -g generator-angular.
```

#### Q. While trying to execute `bower install`

```
bower: command not found
```

Execute the following command first :

```
npm install -g bower
```

#### Q. While trying to execute `gulp dev:runserver`

```
gulp: command not found
```

Execute the following command first

```
npm install -g gulp-cli
```

#### Q. While executing `gulp dev:runserver`

```
events.js:160
throw er; // Unhandled 'error' event
^
Error: Gem sass is not installed.
```

Execute the following command first :

```
gem install sass
```

#### Q. While trying to install `npm config set proxy http://proxy:port` on UBUNTU, I get the following error:

```
ubuntu@ubuntu-Inspiron-3521:~/Desktop/Python-2.7.14$ npm install -g angular-cli
npm ERR! Linux 4.4.0-21-generic
npm ERR! argv "/usr/bin/nodejs" "/usr/bin/npm" "install" "-g" "angular-cli"
npm ERR! node v4.2.6
npm ERR! npm  v3.5.2
npm ERR! code ECONNRESET

npm ERR! network tunneling socket could not be established, cause=getaddrinfo ENOTFOUND proxy proxy:80
npm ERR! network This is most likely not a problem with npm itself
npm ERR! network and is related to network connectivity.
npm ERR! network In most cases you are behind a proxy or have bad network settings.
npm ERR! network
npm ERR! network If you are behind a proxy, please make sure that the
npm ERR! network 'proxy' config is set properly.  See: 'npm help config'

npm ERR! Please include the following file with any support request:
npm ERR!     /home/ubuntu/Desktop/Python-2.7.14/npm-debug.log
```

To solve, execute the following commands:

1. `npm config set registry=registry.npmjs.org`

If the above does not work, try deleting them by following commands:

1. `npm config delete proxy`
2. `npm config delete https-proxy`

Then, start the installation process of frontend once more.

#### Q. While using docker, I am getting the following error on URL [http://localhost:8888/](http://localhost:8888/)

```
Cannot Get \
```

Try removing the docker containers and then building them again.

#### Q. Getting the following error while running `python manage.py seed`

```
Starting the database seeder. Hang on... Exception while running run() in 'scripts.seed' Database successfully seeded
```

Change the python version to 2.7.x . The problem might be because of the python 3.0 version.

#### Q. Getting the following error while executing command `createdb evalai -U postgres`

```
createdb: could not connect to database template1: FATAL: Peer authentication failed for user "postgres"
```

Try creating a new user and then grant all the privileges to it and then create a db.

#### Q. Getting the following error while executing `npm install`

```
npm WARN generator-angular@0.16.0 requires a peer of generator-
karma@>=0.9.0 but none was installed.
```

Uninstall and then install karma again and also don't forget to clean the global as well as project npm cache. Then try again the step 8.

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

#### Q. Getting the following error :

```
ERROR: for db Cannot start service db: driver failed programming external connectivity on endpoint evalai_db_1 (2163096de9aac6561b4f699bb1049acd0ce881fbaa0da28e47cfa9ca0ee1199f): Error starting userland proxy: listen tcp 0.0.0.0:5432: bind: address already in use
```

The following solution only works on Linux.

Execute :
```sudo netstat -lpn |grep :5432```

The output of the above would be in the following form:
```
tcp 0 0 127.0.0.1:5432 0.0.0.0:* LISTEN 25273/postgres
```
Execute the following command:
```
sudo kill 25273 ## This would vary and you can change with the output in the first step
```

#### Q. Getting the following error :
```
ERROR : Version in "./docker-compose.yml" is unsupported. You might be seeing this error becasue you are using wrong Compose file version.
```

Since, the version of compose file is 3. You might be using a docker version which is not compatible. You can upgrade your docker engine and try again.

#### Q. Getting the following error while runnig `python manage.py runserver --settings=settings.dev`
```
Starting the database seeder. Hang on...
Are you sure you want to wipe the existing development database and reseed it? (Y/N)
Exception while running run() in 'scripts.seed'
```

Try clearing the postgres database manually and try again.

#### Q. Getting the following error while executing `gulp dev:runserver`:
```
/usr/lib//nodejs/gulp//bin/gulp.js:132
	gulpInst.start.apply(gulpInst, toRun)l
				   ^	
TypeError: Cannot read properly 'apply of undefined'
```

Execute the following command:
```
rm -rf node_modules/
rm -rf bower_components
npm install
bower install
```
