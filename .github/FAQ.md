## Fequently Asked Questions

### Q1) What is a Test Annotation File?

This is generally a file uploaded by a challenge host and is associated with a challenge phase. This file is used for ranking the submission made by a participant. An annotation file can be shared by more than one challenge phase. In the codebase, this is present as a file field attached to challenge phase model.

### Q2) What to work on EvalAI?

EvalAI’s issue tracker is good place to start. If you find something that interests you, comment on the thread and we’ll help get you started.
Alternatively, if you come across a new bug on the site, please file a new issue and comment if you would like to be assigned. Existing issues are tagged with one or more labels, based on the part of the website it touches, its importance etc., which can help you select one.

### Q3) What are the technologies that EvalAI uses?

### Django
Django is the heart of the application, which powers our backend. We use Django version 1.10.
Django Rest Framework
We use Django Rest Framework for writing and providing REST APIs. It's permission and serializers have helped write a maintainable codebase.

### RabbitMQ
We currently use RabbitMQ for queueing submission messages which are then later on processed by a Python worker.

### PostgreSQL
PostgresSQL is used as our primary datastore. All our tables currently reside in a single database named evalai.

### Angular JS - ^1.6.1
Angular JS is a well-known framework that powers our frontend.

### Task Runner used by us - Gulp

### Q4) How to participate in a challenge?
1. Open the site www.evalai.cloudcv.org.

2. Sign Up and fill in your credentials. Or Login if you have already registered.

3. After Signing Up you would be on the Dashboard page.

4. Then, go to challenges section and choose any challenge which is available.

5. After, you have entered onto the contest page you can go to the Participate tab.

6. Then, you have to create a team of yours and add a team name.

7. After you have added your team, you will see an option in the left section called “My Existing Teams”. Select the team you have registered and click on the participate button.

8. Then you can continue filling your credentials in the contest.

### Q5) “I don’t know Github commands, so what should I do??”

Refer to <li>https://help.github.com/articles/adding-an-existing-project-to-github-using-the-command-line/</li>

### Q6) What to do when coverage decreases in your pull request?

Coverage decreases when the existing test cases don't test the new code you wrote. If you click coverage, you can see exactly which all parts aren't covered and you can write new tests to test the parts. 

## Common Errors during installation

### While using pip install -r dev/requirement.txt:-
```
 Writing manifest file 'pip-egg-info/psycopg2.egg-info/SOURCES.txt'
 Error: You need to install postgresql-server-dev-X.Y for building a server-side extension or libpq-dev for building a client-side application.
 ----------------------------------------
 Command "python setup.py egg_info" failed with error code 1 in /tmp/pip-build-qIjU8G/psycopg2/
```
Use these following commands, this will solve the error:

1. sudo apt-get install postgresql

2. then fire:
sudo apt-get install python-psycopg2

3. and last:
sudo apt-get install libpq-dev

### While using pip install -r dev/requirement.txt:-
```
Command “python setup.py egg_info” failed with error code 1 in /private/var/folders/c7/b45s17816zn_b1dh3g7yzxrm0000gn/T/pip-build- GM2AG/psycopg2/
```

First check have u installed all the mentioned dependencies.
Then, Upgrade the version of postgresql to 10.1..Solved!!

### Getting an import error 

```
Couldn't import Django,"when using command python manage.py migrate --settings=settings.dev.
```

First see have you activated virtualvenv.
Then run pip install django==1.11.8

### Following error :-

```
Can not load reporter “mocha”,it is not registered
```

Uninstall karma and then install  

```
npm uninstall -g generator-karma” && “npm install -g generator-angular.
```
