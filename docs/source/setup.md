# How to setup

EvalAI can run on Linux, Cloud, Windows, and macOS platforms. Use the following list to choose the best installation path for you. The links under *Platform* take you straight to the installation instructions for that platform.

## Installation using Docker

We recommend setting up EvalAI using Docker since there are only two steps involved. If you are not comfortable with docker, feel free to skip this section and move to the manual installation sections given below for different operating systems. Please follow the below steps for setting up using docker:

1. Get the source code on to your machine via git

    ```shell
    git clone https://github.com/Cloud-CV/EvalAI.git evalai && cd evalai
    ```

2. Build and run the Docker containers. This might take a while. You should be able to access EvalAI at `localhost:8888`.

    ```
    docker-compose up --build
    ```

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

* Register and configure Amazon SQS

Follow [these
instructions](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-setting-up.html) for the detailed steps on how to setup Amazon SQS for the production environment.


For setting up a Queue service for development environment download the stand-alone [ElasticMQ distribution](https://s3-eu-west-1.amazonaws.com/softwaremill-public/elasticmq-server-0.14.2.jar). Java 8 or above is required for running the server. Run the following command for which binds to localhost:9324, for running the ElasticMQ Queue service which mocks the Amazon SQS functionality.

```shell
java -jar elasticmq-server-0.14.2.jar
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

### Step 3: Setup codebase

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
python manage.py migrate
```

* For setting up frontend, please make sure that node(`>=7.x.x`), npm(`>=5.x.x`) and bower(`>=1.8.x`) are installed globally on your machine. Install npm and bower dependencies by running

```shell
npm install
bower install
```

### Step 4: Start the development environment

* To run backend development server at [http://127.0.0.1:8000](http://127.0.0.1:8000), simply do:

```
# activate virtual environment if not activated
source venv/bin/activate
python manage.py runserver
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

* Register and configure Amazon SQS

Follow [these
instructions](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-setting-up.html) for the detailed steps on how to setup Amazon SQS for the production environment.


For setting up a Queue service for development environment download the stand-alone [ElasticMQ distribution](https://s3-eu-west-1.amazonaws.com/softwaremill-public/elasticmq-server-0.14.2.jar). Java 8 or above is required for running the server. Run the following command for which binds to localhost:9324, for running the ElasticMQ Queue service which mocks the Amazon SQS functionality.

```shell
java -jar elasticmq-server-0.14.2.jar
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

### Step 3: Setup codebase

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
python manage.py migrate
```

* For setting up frontend, please make sure that node(`>=7.x.x`), npm(`>=5.x.x`) and bower(`>=1.8.x`) are installed globally on your machine. Install npm and bower dependencies by running

```shell
npm install
bower install
```

### Step 4: Start the development environment

* To run backend development server at [backend]

```
# activate virtual environment if not activated
source venv/bin/activate
python manage.py runserver
```

* To run frontend development server for at [frontend]

```
gulp dev:runserver
```
* To run backend development server at [http://127.0.0.1:8000](http://127.0.0.1:8000), simply do:

```
# activate virtual environment if not activated
source venv/bin/activate
python manage.py runserver
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

## Windows Installation Instructions

Setting up EvalAI on your local machine is really easy.
Follow this guide to setup your development machine.

### Step 1: Install prerequisites

* Install Python 2.x, Git, PostgreSQL version >= 9.4, have Amazon SQS configured or ElasticMQ installed and virtualenv, in your computer, if you don't have it already.

### Step 2: Get EvalAI Code

* Get the source code on your machine via git.

    ```shell
    git clone https://github.com/Cloud-CV/EvalAI.git evalai
    ```

### Step 3: Setup the codebase

* Create a python virtual environment and install python dependencies.

    ```shell
    cd evalai
    virtualenv venv
    cd venv/scripts
    activate.bat    # run this command everytime before working on project
    cd ../..
    pip install -r requirements/dev.txt
    ```

* Rename `settings/dev.sample.py` as `dev.py` and change credential in `settings/dev.py`

    ```
    cp settings/dev.sample.py settings/dev.py
    ```
    Use your postgres username and password for fields `USER` and `PASSWORD` in `dev.py` file. 

* Create an empty postgres database and run database migration.
    Make sure you have defined the PostgreSql path to the Environment Variables.
    
    ```
    createdb evalai
    ```
    Enter your password for authentication and a new database will be added.
    ```
    python manage.py migrate
    ```

* Seed the database with some fake data to work with.

    ```
    python manage.py seed
    ```
    This command also creates a `superuser(admin)`, a `host user` and a `participant user` with following credentials.

    **SUPERUSER-** username: `admin` password: `password`  
    **HOST USER-** username: `host` password: `password`  
    **PARTICIPANT USER-** username: `participant` password: `password`

    By default the seed commands seeds the database with only one challenge. Which can be changed by passing the argument
    `-nc` along with the number of challenges you want to seed the database with.

    For example, suppose I want to seed the database with 5 challenges. I would run the command

    ```
    python manage.py seed -nc 5
    ```

    This would seed the database with 5 different challenges.

### Step 4: Start the development environment

* That's it. Now you can run development server at [http://127.0.0.1:8000] (for serving backend)

    ```
    python manage.py runserver
    ```


* Open a new cmd window with node>=(7.0.0) installed on your machine and type

    ```
    npm install
    ``` 

* Install bower(1.8.0) globally by running:

	```
	npm install -g bower
	```

* Now install the bower dependencies by running:

	```
	bower install
	```

* If you running npm install behind a proxy server, use

	```
	npm config set proxy http://proxy:port
	```

* Now to connect to dev server at [http://127.0.0.1:8888] (for serving frontend)

    ```
    gulp dev:runserver
    ```

* That's it, Open web browser and hit the url [http://127.0.0.1:8888].

[link]: http://stackoverflow.com/a/28938258/2534102
[backend]: http://127.0.0.1:8000
[frontend]: http://127.0.0.1:8888
[http://127.0.0.1:8000]: http://127.0.0.1:8000
[http://127.0.0.1:8888]: http://127.0.0.1:8888
