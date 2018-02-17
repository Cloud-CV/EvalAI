<p align="center"><img width="65%" src="docs/source/\_static/img/evalai_logo.png" /></p>

------------------------------------------------------------------------------------------

[![Join the chat at https://gitter.im/Cloud-CV/EvalAI](https://badges.gitter.im/Cloud-CV/EvalAI.svg)](https://gitter.im/Cloud-CV/EvalAI?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
[![Build Status](https://travis-ci.org/Cloud-CV/EvalAI.svg?branch=master)](https://travis-ci.org/Cloud-CV/EvalAI)
[![Coverage Status](https://coveralls.io/repos/github/Cloud-CV/EvalAI/badge.svg)](https://coveralls.io/github/Cloud-CV/EvalAI)
[![Requirements Status](https://requires.io/github/Cloud-CV/EvalAI/requirements.svg?branch=master)](https://requires.io/github/Cloud-CV/EvalAI/requirements/?branch=master)
[![Code Health](https://landscape.io/github/Cloud-CV/EvalAI/master/landscape.svg?style=flat)](https://landscape.io/github/Cloud-CV/EvalAI/master)
[![Code Climate](https://codeclimate.com/github/Cloud-CV/EvalAI/badges/gpa.svg)](https://codeclimate.com/github/Cloud-CV/EvalAI)
[![Documentation Status](https://readthedocs.org/projects/markdown-guide/badge/?version=latest)](http://evalai.readthedocs.io/en/latest/)


EvalAI is an open source web application that helps researchers, students and data-scientists to create, collaborate and participate in various AI challenges organized round the globe.

In recent years, it has become increasingly difficult to compare an algorithm solving a given task with other existing approaches. These comparisons suffer from minor differences in algorithm implementation, use of non-standard dataset splits and different evaluation metrics. By providing a central leaderboard and submission interface, we make it easier for researchers to reproduce the results mentioned in the paper and perform reliable & accurate quantitative analysis. By providing swift and robust backends based on map-reduce frameworks that speed up evaluation on the fly, EvalAI aims to make it easier for researchers to reproduce results from technical papers and perform reliable and accurate analyses.

<p align="center"><img width="65%" src="docs/source/\_static/img/kaggle_comparison.png" /></p>

A question we’re often asked is: Doesn’t Kaggle already do this? The central differences are:

- **Custom Evaluation Protocols and Phases**: We have designed versatile backend framework that can support user-defined evaluation metrics, various evaluation phases, private and public leaderboard.

- **Faster Evaluation**: The backend evaluation pipeline is engineered so that submissions can be evaluated parallelly using multiple cores on multiple machines via mapreduce frameworks offering a significant performance boost over similar web AI-challenge platforms.

- **Portability**: Since the platform is open-source, users have the freedom to host challenges on their own private servers rather than having to explicitly depend on Cloud Services such as AWS, Azure, etc.

- **Easy Hosting**: Hosting a challenge is streamlined. One can create the challenge on EvalAI using the intuitive UI (work-in-progress) or using zip configuration file.

- **Centralized Leaderboard**: Challenge Organizers whether host their challenge on EvalAI or forked version of EvalAI, they can send the results to main EvalAI server. This helps to build a centralized platform to keep track of different challenges. 

## Goal

Our ultimate goal is to build a centralized platform to host, participate and collaborate in AI challenges organized around the globe and we hope to help in benchmarking progress in AI.

## Performance comparison

Some background: Last year, the [Visual Question Answering Challenge (VQA, 2016](http://www.visualqa.org/vqa_v1_challenge.html) was hosted on some other platform, and on average evaluation would take **~10 minutes**. EvalAI hosted this year's [VQA Challenge 2017](https://evalai.cloudcv.org/featured-challenges/1/overview). This year, the dataset for the [VQA Challenge 2017](http://www.visualqa.org/challenge.html) is twice as large. Despite this, we’ve found that our parallelized backend only takes **~130 seconds** to evaluate on the whole test set VQA 2.0 dataset.

## Installation Instructions

Setting up EvalAI on your local machine is really easy. You can setup EvalAI using two methods:

### Using Docker

You can also use Docker Compose to run all the components of EvalAI together. The steps are:

1. Get the source code on to your machine via git.

    ```shell
    git clone https://github.com/Cloud-CV/EvalAI.git evalai && cd evalai
    ```

2. Rename `settings/dev.sample.py` as `dev.py` and change credential in `settings/dev.py`

    ```
    cp settings/dev.sample.py settings/dev.py
    ```
    Use your postgres username and password for fields `USER` and `PASSWORD` in `dev.py` file.

3. Build and run the Docker containers. This might take a while. You should be able to access EvalAI at `localhost:8888`.

    ```
    docker-compose -f docker-compose.dev.yml up -d --build
    ```

### Using Virtual Environment

1. Install [python] 2.x (EvalAI only supports python2.x for now.), [git], [postgresql] version >= 10.1, [RabbitMQ] and [virtualenv], in your computer, if you don't have it already.
*If you are having trouble with postgresql on Windows check this link [postgresqlhelp].*

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

4. Rename `settings/dev.sample.py` as `dev.py` and change credential in `settings/dev.py`

    ```
    cp settings/dev.sample.py settings/dev.py
    ```
    Use your postgres username and password for fields `USER` and `PASSWORD` in `dev.py` file.

5. Create an empty postgres database and run database migration.

    ```
    sudo -i -u (username)
    createdb evalai
    python manage.py migrate --settings=settings.dev
    ```

6. Seed the database with some fake data to work with.

    ```
    python manage.py seed --settings=settings.dev
    ```
    This command also creates a `superuser(admin)`, a `host user` and a `participant user` with following credentials.

    **SUPERUSER-** username: `admin` password: `password`  
    **HOST USER-** username: `host` password: `password`  
    **PARTICIPANT USER-** username: `participant` password: `password`    

7. That's it. Now you can run development server at [http://127.0.0.1:8000] (for serving backend)

    ```
    python manage.py runserver --settings=settings.dev
    ```


8. Open a new terminal window with node(6.9.2) and ruby(gem) installed on your machine and type

    ```
    npm install
    ``` 
    Install bower(1.8.0) globally by running:
    ```
    npm install -g bower
    ```
    Now install the bower dependencies by running:
    ```
    bower install
    ```
    If you running npm install behind a proxy server, use
    ```
    npm config set proxy http://proxy:port
    ```
9. Now to connect to dev server at [http://127.0.0.1:8888] (for serving frontend)

    ```
    gulp dev:runserver
    ```

10. That's it, Open web browser and hit the url [http://127.0.0.1:8888].

11. (Optional) If you want to see the whole game into play, then start the RabbitMQ worker in a new terminal window using the following command that consumes the submissions done for every challenge:

    ```
    python scripts/workers/submission_worker.py
    ```

## The Team

EvalAI is currently maintained by [Deshraj Yadav](https://deshraj.github.io), [Akash Jain](http://www.jainakash.in/), [Taranjeet Singh](http://taranjeet.github.io/), [Shiv Baran Singh](http://www.shivbaran.in/) and [Rishabh Jain](https://rishabhjain2018.github.io/). A non-exhaustive list of other major contributors includes: Harsh Agarwal, Prithvijit Chattopadhyay, Devi Parikh and Dhruv Batra.

## Contribution guidelines

If you are interested in contributing to EvalAI, follow our [contribution guidelines](https://github.com/Cloud-CV/EvalAI/blob/master/.github/CONTRIBUTING.md).

[python]: https://www.python.org/download/releases/2.7/
[git]: https://git-scm.com/downloads
[virtualenv]: https://virtualenv.pypa.io/
[postgresql]: http://www.postgresql.org/download/
[postgresqlhelp]: http://bobbyong.com/blog/installing-postgresql-on-windoes/
[rabbitmq]: https://www.rabbitmq.com/
[http://127.0.0.1:8888]: http://127.0.0.1:8888
[http://127.0.0.1:8000]: http://127.0.0.1:8000
