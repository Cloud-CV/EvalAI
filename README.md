# EvalAI-ngx
Revamped codebase of EvalAI Frontend

<p align="center"><img width="65%" src="src/assets/images/evalai_logo.png" /></p>

------------------------------------------------------------------------------------------

[![Join the chat at https://gitter.im/Cloud-CV/EvalAI](https://badges.gitter.im/Cloud-CV/EvalAI.svg)](https://gitter.im/Cloud-CV/EvalAI?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
[![codecov](https://codecov.io/gh/Cloud-CV/EvalAI-ngx/branch/master/graph/badge.svg)](https://codecov.io/gh/Cloud-CV/EvalAI-ngx)
[![Build Status](https://travis-ci.org/Cloud-CV/EvalAI-ngx.svg?branch=master)](https://travis-ci.org/Cloud-CV/EvalAI-ngx)

EvalAI is an open source web application that helps researchers, students and data-scientists to create, collaborate and participate in various AI challenges organized round the globe.

In recent years, it has become increasingly difficult to compare an algorithm solving a given task with other existing approaches. These comparisons suffer from minor differences in algorithm implementation, use of non-standard dataset splits and different evaluation metrics. By providing a central leaderboard and submission interface, we make it easier for researchers to reproduce the results mentioned in the paper and perform reliable & accurate quantitative analysis. By providing swift and robust backends based on map-reduce frameworks that speed up evaluation on the fly, EvalAI aims to make it easier for researchers to reproduce results from technical papers and perform reliable and accurate analyses.

<p align="center"><img width="65%" src="src/assets/images/kaggle_comparison.png" /></p>

A question we’re often asked is: Doesn’t Kaggle already do this? The central differences are:

- **Custom Evaluation Protocols and Phases**: We have designed versatile backend framework that can support user-defined evaluation metrics, various evaluation phases, private and public leaderboard.

- **Faster Evaluation**: The backend evaluation pipeline is engineered so that submissions can be evaluated parallelly using multiple cores on multiple machines via mapreduce frameworks offering a significant performance boost over similar web AI-challenge platforms.

- **Portability**: Since the platform is open-source, users have the freedom to host challenges on their own private servers rather than having to explicitly depend on Cloud Services such as AWS, Azure, etc.

- **Easy Hosting**: Hosting a challenge is streamlined. One can create the challenge on EvalAI using the intuitive UI (work-in-progress) or using zip configuration file.

- **Centralized Leaderboard**: Challenge Organizers whether host their challenge on EvalAI or forked version of EvalAI, they can send the results to main EvalAI server. This helps to build a centralized platform to keep track of different challenges. 

## Goal

Our ultimate goal is to build a centralized platform to host, participate and collaborate in AI challenges organized around the globe and we hope to help in benchmarking progress in AI.

## Performance comparison

Some background: Last year, the [Visual Question Answering Challenge (VQA) 2016](http://www.visualqa.org/vqa_v1_challenge.html) was hosted on some other platform, and on average evaluation would take **~10 minutes**. EvalAI hosted this year's [VQA Challenge 2017](https://evalai.cloudcv.org/featured-challenges/1/overview). This year, the dataset for the [VQA Challenge 2017](http://www.visualqa.org/challenge.html) is twice as large. Despite this, we’ve found that our parallelized backend only takes **~130 seconds** to evaluate on the whole test set VQA 2.0 dataset.

## Installation Instructions

Setting up EvalAI-ngx on your local machine is really easy.
Follow this guide to setup your development machine.

Get the source code on your machine via git
```
git clone git@github.com:Cloud-CV/EvalAI-ngx.git
```
If you have not added [ssh key](https://help.github.com/articles/adding-a-new-ssh-key-to-your-github-account/) to your GitHub account then get the source code by running the following command
```
git clone https://github.com/Cloud-CV/EvalAI-ngx
```

```
npm install -g @angular/cli
cd EvalAI-ngx/
npm install
```

## Development

### For Running on localhost:

Run `ng serve` for a dev server. Navigate to `http://localhost:4200/`. The app will automatically reload if you change any of the source files.

### Backend for localhost:

Setting up EvalAI on your local machine is really easy. You can setup EvalAI using docker:
The steps are:

1. Install [docker](https://docs.docker.com/install/linux/docker-ce/ubuntu/) and [docker-compose](https://docs.docker.com/compose/install/) on your machine.

2. Get the source code on to your machine via git.

    ```shell
    git clone https://github.com/Cloud-CV/EvalAI.git evalai && cd evalai
    ```

3. Build and run the Docker containers. This might take a while.

    ```
    docker-compose up --build
    ```

4. That's it. Open web browser and hit the url [http://127.0.0.1:8888](http://127.0.0.1:8888). Three users will be created by default which are listed below -
    
    **SUPERUSER-** username: `admin` password: `password`  
    **HOST USER-** username: `host` password: `password`  
    **PARTICIPANT USER-** username: `participant` password: `password`

If you are facing any issue during installation, please see our [common errors during installation page](https://evalai.readthedocs.io/en/latest/faq(developers).html#common-errors-during-installation).


### For deploying with [Surge](https://surge.sh/):

Surge will automatically generate deployment link whenever a pull request passes Travis CI. 

Suppose pull request number is 123 and it passes Travis CI. The deployment link can be found here: `https://pr-123-evalai.surge.sh`

## Code scaffolding

Run `ng generate component component-name` to generate a new component. You can also use `ng generate directive|pipe|service|class|guard|interface|enum|module`.

## Code Documentation

We are using [compodoc](https://compodoc.github.io/website/guides/jsdoc-tags.html) for documentation. The goal of this tool is to generate a documentation for all the common APIs of the application like modules, components, injectables, routes, directives, pipes and classical classes.

Compodoc supports [these](https://compodoc.github.io/website/guides/jsdoc-tags.html) JSDoc tags.

## Contributing

Please go through our [Contribution Guidelines](https://github.com/Cloud-CV/EvalAI/blob/master/.github/CONTRIBUTING.md). Also go through our detailed [Code Structure Guide](https://github.com/Cloud-CV/EvalAI-ngx/blob/master/.github/CODE_STRUCTURE.md) to make the most of existing re-usable features. Finally, go through the [Pull Request Template](https://github.com/Cloud-CV/EvalAI-ngx/blob/master/.github/PULL_REQUEST_TEMPLATE.md) when creating your pull request.



### Building and Serving the documentation

Run the following command to build and serve the docs:
```
npm run doc:buildandserve
```
Open http://localhost:8080 in the browser to have a look at the generated docs.

## Build

Run `ng build` to build the project. The build artifacts will be stored in the `dist/` directory. Use the `-prod` flag for a production build.

## Running unit tests

Run `ng test` to execute the unit tests via [Karma](https://karma-runner.github.io).

## Running end-to-end tests

Run `ng e2e` to execute the end-to-end tests via [Protractor](http://www.protractortest.org/).

### Setup using Docker

You can also use Docker Compose to run all the components of EvalAI-ngx together. The steps are:

1. Get the source code on to your machine via git.

    ```shell
    git clone https://github.com/Cloud-CV/EvalAI-ngx.git && cd EvalAI-ngx
    ```

2. Build and run the Docker containers. This might take a while. You should be able to access EvalAI at `localhost:8888`.

    ```
    docker-compose -f docker-compose.dev.yml up -d --build
    ```

## The Team

EvalAI-ngx is currently maintained by [Shekhar Rajak](http://s-hacker.info/), [Mayank Lunayach](https://github.com/lunayach), [Shivani Prakash Gupta](https://www.behance.net/shivaniprakash19), [Rishabh Jain](https://rishabhjain2018.github.io/) and [Deshraj Yadav](https://deshraj.github.io).
