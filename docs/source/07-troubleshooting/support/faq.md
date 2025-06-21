# FAQs (Frequently Asked Questions)

This section provides answers to common questions developers have while working with or contributing to EvalAI. It is organized by category to help you find answers quickly.

## Table of Contents

- [Setup & Installation](#setup-installation)
- [Docker & Frontend Issues](#docker-frontend-issues)
- [Python & Backend Errors](#python-backend-errors)
- [Development & Contribution](#development-contribution)
- [Logs & Debugging](#logs-debugging)
- [Command Node, npm & Frontend Issues](#common-node-npm-frontend-issues)
- [Proxy / Network Issues](#proxy-network-issues)
- [PostgreSQL Errors](#postgresql-errors)
- [Learning Resources](#learning-resources)
- [Recommended Next Steps](#recommended-next-steps)

## Setup & Installation

### Q. How to start contributing?

EvalAI’s issue tracker is good place to start. If you find something that interests you, comment on the thread and we’ll help get you started.
Alternatively, if you come across a new bug on the site, please file a new issue and comment if you would like to be assigned. Existing issues are tagged with one or more labels, based on the part of the website it touches, its importance etc., which can help you select one.

### Q. What are the technologies that EvalAI uses?

Please refer to [Technologies Used](https://evalai.readthedocs.io/en/latest/architecture.html)

### Q. Why was `virtualenv` setup deprecated?

Due to evolving dependencies and environment complexity, we now recommend using Docker-based setup for reliability and consistency across systems.

## Docker & Frontend Issues

### Q. I see `Cannot GET \` on `http://localhost:8888/` when using Docker.

This may happen if the container is not built properly. Run:

```
docker compose down
docker compose up --build
```

### Q. I get this error: `ERROR: Version in "./docker-compose.yml" is unsupported`.

Upgrade your Docker engine to the latest version compatible with Compose file version 3.

### Q. While building EvalAI via Docker, I get:
```
ERROR: Service 'celery' failed to build: pull access denied for evalai_django, repository does not exist or may require 'docker login': denied: requested access to the resource is denied
```

Ensure that your directory is named `evalai` (all lowercase). Docker image naming depends on the folder name. For instance, the image evalai_django gets renamed to evalai_dev_django if your directory is renamed to EvalAI_dev. 

## Python & Backend Errors

### Q. I get this error during DB seeding:

```bash
Exception while running run() in 'scripts.seed'
```

Try deleting the PostgreSQL database manually or ensure you're using Python 2.7.x (not Python 3.x).

### Q. I see `Peer authentication failed for user "postgres"` when using `createdb`.

Try creating a new user and then grant all the privileges to it and then create a db.


### Q. I get this error while running tests inside Docker:

```
import file mismatch...
```

Clean __pycache__ and .pyc files:

```
find . | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf
```

## Development & Contribution

### Q. How do I fix coverage decrease warnings?

This means your new code isn't covered by tests. Click on the coverage report to view uncovered lines and add test cases accordingly.

## Logs & Debugging

### Q. How do I debug `psycopg2` installation errors while using `pip install -r dev/requirement.txt`?

Error:

```
Error: You need to install postgresql-server-dev-X.Y...
```

Fix:

```
sudo apt-get install postgresql
sudo apt-get install python-psycopg2
sudo apt-get install libpq-dev
```

## Common Node, npm & Frontend Issues

### Q. `gulp: command not found`

```
npm install -g gulp-cli
```

### Q. `bower: command not found`

```
npm install -g bower
```

### Q. Mocha reporter not loading:

```
npm uninstall -g generator-karma
npm install -g generator-angular
```

### Q. Error: `Gem sass is not installed` while executing `gulp dev:runserver`

```
gem install sass
```

### Q. Getting `karma@>=0.9.0 but none was installed` while executing `npm install`:

Reinstall after removing cache:

```
npm uninstall karma
npm install karma
npm cache clean --force
```

### Q. Getting:

```
/usr/lib//nodejs/gulp//bin/gulp.js:132
TypeError: Cannot read properly 'apply of undefined'
```

Fix:

```
rm -rf node_modules/ bower_components
npm install
bower install
```

## Proxy / Network Issues

### Q. npm install fails with ECONNRESET or tunneling error

Fix your proxy settings:

```
npm config delete proxy
npm config delete https-proxy
npm config set registry https://registry.npmjs.org/
```

## PostgreSQL Errors

### Q. ERROR: Port 5432 already in use

Check and kill the process:

```
sudo netstat -lpn | grep :5432
sudo kill <PID>
```

## Learning Resources

- [Git and GitHub Learning Resources](https://help.github.com/articles/git-and-github-learning-resources/)

- [Markdown Guide](https://guides.github.com/features/mastering-markdown/)


## Recommended Next Steps

- Refer to the [EvalAI Docs](https://evalai.readthedocs.io/en/latest/)

- [Join our Slack](https://join.slack.com/t/cloudcv-community/shared_invite/zt-3252n6or8-e0QuZKIZFLB0zXtQ6XgxfA) to ask for help if you're stuck