# Details to setup EvalAI for Development and Production

The first thing you need to do is enable EvalAI in your TraviCI dashboard so that all builds will be covered by TravisCI.

### Step 1
#### Create .travis.yml file

Add the following code to the file (taken from the existing EvalAI repo):

```
language: python
sudo: false
services:
- docker
python:
- '3.6'
addons:
  postgresql: '10'
  apt:
    update: true
    packages:
    - postgresql-10
    - postgresql-client-10
    - default-jre # Java11 is used for elasticmq
    - libgnutls28-dev
env:
  global:
  - PGPORT=5432
cache:
  directories:
  - "$HOME/.cache/pip"
before_cache:
- rm -f $HOME/.cache/pip/log/debug.log
before_script:
- npm install
- npm install -g bower
- npm install -g gulp
- npm install -g karma-cli
- bower install
- gulp dev
- sudo sed -i 's/port = 5433/port = 5432/' /etc/postgresql/10/main/postgresql.conf
- sudo cp /etc/postgresql/{9.4,10}/main/pg_hba.conf
- sudo service postgresql restart
- psql -c "CREATE DATABASE evalai" -U postgres
- wget https://s3-eu-west-1.amazonaws.com/softwaremill-public/elasticmq-server-0.14.2.jar
- java -jar elasticmq-server-0.14.2.jar &
before_install:
- sudo rm -f /etc/boto.cfg
- export CHROME_BIN=chromium-browser
- export DISPLAY=:99.0
services:
- xvfb
install:
- pip install -r requirements/dev.txt
- pip install awscli==1.16.57 coveralls
script:
- flake8 ./
- karma start --single-run
- py.test --cov . --cov-config .coveragerc
after_success:
- bash <(curl -s https://codecov.io/bash)
- coveralls --rcfile=.coveragerc
- ./scripts/deployment/push.sh
notifications:
  email:
    on_success: change
    on_failure: always
    slack: cloudcv:gy3CGQGNXLwXOqVyzXGZfdea
```

# Step 2
#### Specify conditions for deploy for development and production and add command to specify code to push per condition

To setup TravisCI for dev and prod we could have seperate branches to push to. We will set the deploy commands for each branch.

##### Example for Production

```
deploy:
  provider: s3
  on:
    branch: production
```

The above will only run if the branch is set to production because the deploy command will only run id all conditions in the `on` section are met.

##### Example for Deployment

```
deploy:
  provider: localhost
  on:
    branch: deployment
```

The above will only run if the branch is set to deployment because the deploy command will only run id all conditions in the `on` section are met.

### It must not be only branches other conditions could be used. Other conditions could be used in the `on:` section.

Example

```
deploy:
  provider: s3
  acces_key_id = "Key ID"
  secret_access_key = "Secret"
  bucket: "S3 Bucket"
  on:
    condition: "$CC = gcc"
 ```
 
 The above will only run is the env variable `$CC` is set to gcc.
 
 This is the way EvalAI could be setup with Travis for Development anf Production. We just have to set the conditions for the deploy section



