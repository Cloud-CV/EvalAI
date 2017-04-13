## How to setup

This section guides first-time contributor through installing the EvalAI development environment on Ubuntu(recommended 14.04)

###Step 1: Install prerequisites

* Install git

```shell
sudo apt-get install git
```

* Install postgres

```shell
sudo apt-get install postgresql libpq-dev
```

* Install rabbitmq

```shell
echo 'deb http://www.rabbitmq.com/debian/ stable main' | sudo tee /etc/apt/sources.list.d/rabbitmq.list
sudo apt-get update
sudo apt-get install rabbitmq-server
```

* Install virtualenv

```shell
# only if pip is not installed
sudo apt-get install python-pip python-dev build-essential
# upgrade pip, not necessary
sudo pip install --upgrade pip
# upgrade virtualenv
sudo pip install --upgrade virtualenv
```

###Step 2: Get EvalAI code

If you haven't already created an ssh key and added it to your GitHub account,
you should do that now by following [these
instructions](https://help.github.com/articles/connecting-to-github-with-ssh/).

* In your browser, visit [https://github.com/Cloud-CV/EvalAI](https://github.com/Cloud-CV/EvalAI) and click the `fork` button. You will need to be logged in to GitHub to do this.

* Open Terminal and clone your fork by

```shell
git clone git@github.com:YOUR_GITHUB_USER_NAME/EvalAI.git evalai
```

Don't forget to replace YOUR_GITHUB_USER_NAME with your git username.


###Step 3: Setup code base

* Create a python virtual environment and install python dependencies.

```shell
cd evalai
virtualenv venv
source venv/bin/activate
pip install -r requirements/dev.txt
```

* Rename `settings/dev.sample.py` as `dev.py`

```
cp settings/dev.sample.py settings/dev.py
```

* Create an empty postgres database and run database migration.

```
createdb evalai -U postgres
# update postgres user password
psql -U postgres -c "ALTER USER postgres PASSWORD 'postgres';"
# run migrations
python manage.py migrate --settings=settings.dev
```

* For setting up frontend, run

```shell
npm install
bower install
```

###Step 4: Start the development environment

* To run backend development server at `http://127.0.0.1:8000`[http://127.0.0.1:8000]

```
# activate virtual environment if not activated
source venv/bin/activate
python manage.py runserver --settings=settings.dev
```

* To run frontend development server for at `http://127.0.0.1:8888`[http://127.0.0.1:8888]

```
gulp dev:runserver
```

### Common Errors

#### Error: You need to install postgresql-server-dev-X.Y for building a server-side extension or libpq-dev for building a client-side application.

__Solution__: Install libpq-dev

```shell
sudo apt-get install libpq-dev
```

Possible solutions for the same problem can be found at [link]


[link]: http://stackoverflow.com/a/28938258/2534102
[backend]: http://127.0.0.1:8000
[frontend]: http://127.0.0.1:8888
