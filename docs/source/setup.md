# How to setup

EvalAI can run on Linux, Cloud, Windows, and macOS platforms. Use the following list to choose the best installation path for you. The links under *Platform* take you straight to the installation instructions for that platform.

## Ubuntu Installation Instructions

### Step 1: Install prerequisites

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

### Step 2: Get EvalAI code

If you haven't already created an ssh key and added it to your GitHub account,
you should do that now by following [these
instructions](https://help.github.com/articles/connecting-to-github-with-ssh/).

* In your browser, visit [https://github.com/Cloud-CV/EvalAI](https://github.com/Cloud-CV/EvalAI) and click the `fork` button. You will need to be logged in to GitHub to do this.

* Open Terminal and clone your fork by

```shell
git clone git@github.com:YOUR_GITHUB_USER_NAME/EvalAI.git evalai
```

Don't forget to replace `YOUR_GITHUB_USER_NAME` with your git username.

### Step 3: Setup code base

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

### Step 4: Start the development environment

* To run backend development server at [http://127.0.0.1:8000](http://127.0.0.1:8000), simply do:

```
# activate virtual environment if not activated
source venv/bin/activate
python manage.py runserver --settings=settings.dev
```

* To run frontend development server at [http://127.0.0.1:8888](http://127.0.0.1:8888), simply do:

```
gulp dev:runserver
```

## Fedora Installation Instructions

### Step 1: Install prerequisites

* Install git

```shell
sudo yum install git-all
```

* Install postgres

```shell
sudo yum install postgresql postgresql-devel
```
If you still encounter issues with pg_config, you may need to add it to your PATH, i.e.
```shell
export PATH=$PATH:/usr/pgsql-x.x/bin
```
where `x.x` is your version, such as /usr/pgsql-9.5./bin.

* Install rabbitmq

```shell
# use the below commands to get Erlang on our system:
wget http://dl.fedoraproject.org/pub/epel/6/x86_64/epel-release-6-8.noarch.rpm
wget http://rpms.famillecollet.com/enterprise/remi-release-6.rpm
sudo rpm -Uvh remi-release-6*.rpm epel-release-6*.rpm
# Finally, download and install Erlang:
sudo yum install -y erlang
# Once we have Erlang, we can continue with installing RabbitMQ:
wget http://www.rabbitmq.com/releases/rabbitmq-server/v3.2.2/rabbitmq-server-3.2.2-1.noarch.rpm
rpm --import http://www.rabbitmq.com/rabbitmq-signing-key-public.asc
sudo yum install rabbitmq-server-3.2.2-1.noarch.rpm
```

* Install virtualenv

```shell
sudo yum -y install python-pip python-devel groupinstall 'Development Tools'
# upgrade pip, not necessary
sudo pip install --upgrade pip
# upgrade virtualenv
sudo pip install --upgrade virtualenv
```

### Step 2: Get EvalAI code

If you haven't already created an ssh key and added it to your GitHub account,
you should do that now by following [these
instructions](https://help.github.com/articles/connecting-to-github-with-ssh/).

* In your browser, visit [https://github.com/Cloud-CV/EvalAI](https://github.com/Cloud-CV/EvalAI) and click the `fork` button. You will need to be logged in to GitHub to do this.

* Open Terminal and clone your fork by

```shell
git clone git@github.com:YOUR_GITHUB_USER_NAME/EvalAI.git evalai
```

Don't forget to replace `YOUR_GITHUB_USER_NAME` with your git username.

### Step 3: Setup code base

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
curl -sL https://rpm.nodesource.com/setup_6.x | sudo -E bash -
sudo yum install nodejs
npm install -g bower
```

### Step 4: Start the development environment

* To run backend development server at [backend]

```
# activate virtual environment if not activated
source venv/bin/activate
python manage.py runserver --settings=settings.dev
```

* To run frontend development server for at [frontend]

```
gulp dev:runserver
```
* To run backend development server at [http://127.0.0.1:8000](http://127.0.0.1:8000), simply do:

```
# activate virtual environment if not activated
source venv/bin/activate
python manage.py runserver --settings=settings.dev
```

* To run frontend development server at [http://127.0.0.1:8888](http://127.0.0.1:8888), simply do:

```
gulp dev:runserver
```

### Common Errors

__Error__: *You need to install postgresql-server-dev-X.Y for building a server-side extension or libpq-dev for building a client-side application.*

__Solution__: Install libpq-dev

```shell
sudo apt-get install libpq-dev
```

Possible solutions for the same problem can be found at [link].

## Installation using Docker

You can also use Docker Compose to run all the components of EvalAI together. The steps are:

1. Get the source code on to your machine via git.

    ```shell
    git clone https://github.com/Cloud-CV/EvalAI.git evalai && cd evalai
    ```

2. Build and run the Docker containers. This might take a while. You should be able to access EvalAI at `localhost:8888`.

    ```
    docker-compose -f docker-compose.dev.yml up -d --build
    ```

[link]: http://stackoverflow.com/a/28938258/2534102
[backend]: http://127.0.0.1:8000
[frontend]: http://127.0.0.1:8888
