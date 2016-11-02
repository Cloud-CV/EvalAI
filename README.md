# EvalAI

[![Build Status](https://travis-ci.org/Cloud-CV/EvalAI.svg?branch=master)](https://travis-ci.org/Cloud-CV/EvalAI)
[![Coverage Status](https://coveralls.io/repos/github/Cloud-CV/EvalAI/badge.svg)](https://coveralls.io/github/Cloud-CV/EvalAI)
[![Requirements Status](https://requires.io/github/Cloud-CV/EvalAI/requirements.svg?branch=master)](https://requires.io/github/Cloud-CV/EvalAI/requirements/?branch=master)
[![Code Health](https://landscape.io/github/Cloud-CV/EvalAI/master/landscape.svg?style=flat)](https://landscape.io/github/Cloud-CV/EvalAI/master)
[![Code Climate](https://codeclimate.com/github/Cloud-CV/EvalAI/badges/gpa.svg)](https://codeclimate.com/github/Cloud-CV/EvalAI)


EvalAI is an open source web application that helps researchers, students and data-scientists to create, collaborate and participate in various AI challenges organized round the globe. 

## How to setup

Setting up EvalAI on your local machine is really easy. 
Follow this guide to setup your development machine.

1. Install [git], [postgresql] and [virtualenv], in your computer, if you don't have it already.

2. Get the source code on your machine via git.
    
    ```shell
    git clone https://github.com/Cloud-CV/EvalAI.git evalai
    ```

3. Create a python virtual environment and install python dependencies.

    ```shell
    cd evalai
    virtualenv venv
    source venv/bin/activate  # run this command everytime before working on project
    pip install -r requirements/dev.txt
    ```

4. Change credential in setting/dev.py
    
    ```
    nano settings/dev.py
    ```
    For new postgresql user  
    
    USER: "postgres";PASSWORD: ""

5. Create an empty postgres database and run database migration.

    ```
    createdb evalai
    python manage.py migrate
    python manage.py sample_data
    ```

6. That's it. Now you can run development server at http://127.0.0.1:8000

    ```
    python manage.py runserver --settings=settings.dev
    ```

## Contribution guidelines

If you are interested in contributing to EvalAI, follow your [contribution guidelines](https://github.com/Cloud-CV/EvalAI/blob/development/CONTRIBUTING.md).

[git]: https://git-scm.com/downloads
[virtualenv]: https://virtualenv.pypa.io/
[postgresql]: http://www.postgresql.org/download/
