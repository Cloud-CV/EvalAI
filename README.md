<p align="center"><img width="65%" src="docs/source/\_static/img/evalai_logo.png" /></p>

------------------------------------------------------------------------------------------

[![Join the chat at https://gitter.im/Cloud-CV/EvalAI](https://badges.gitter.im/Cloud-CV/EvalAI.svg)](https://gitter.im/Cloud-CV/EvalAI?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
[![Build Status](https://travis-ci.org/Cloud-CV/EvalAI.svg?branch=master)](https://travis-ci.org/Cloud-CV/EvalAI)
[![Coverage Status](https://coveralls.io/repos/github/Cloud-CV/EvalAI/badge.svg)](https://coveralls.io/github/Cloud-CV/EvalAI)
[![Requirements Status](https://requires.io/github/Cloud-CV/EvalAI/requirements.svg?branch=master)](https://requires.io/github/Cloud-CV/EvalAI/requirements/?branch=master)
[![Code Health](https://landscape.io/github/Cloud-CV/EvalAI/master/landscape.svg?style=flat)](https://landscape.io/github/Cloud-CV/EvalAI/master)
[![Code Climate](https://codeclimate.com/github/Cloud-CV/EvalAI/badges/gpa.svg)](https://codeclimate.com/github/Cloud-CV/EvalAI)
[![Documentation Status](https://readthedocs.org/projects/markdown-guide/badge/?version=latest)](http://evalai.readthedocs.io/en/latest/)

EvalAI is an open source platform for evaluating and comparing machine learning (ML) and artificial intelligence (AI) algorithms at scale. 

In recent years, it has become increasingly difficult to compare an algorithm solving a given task with other existing approaches. These comparisons suffer from minor differences in algorithm implementation, use of non-standard dataset splits and different evaluation metrics. By providing a central leaderboard and submission interface, we make it easier for researchers to reproduce the results mentioned in the paper and perform reliable & accurate quantitative analysis. By providing swift and robust backends based on map-reduce frameworks that speed up evaluation on the fly, EvalAI aims to make it easier for researchers to reproduce results from technical papers and perform reliable and accurate analyses.

The features offered by us are - 

- **Custom Evaluation Protocols and Phases**: We allow creation of an arbitrary number of evaluation phases and dataset splits, compatibility using any programming language, and organizing results in both public and private leaderboards.

- **Remote Evaluation**: Certain large-scale challenges need special compute capabilities for evaluation. If the challenge needs extra computational power, challenge organizers can easily add their own cluster of worker nodes to process participant submissions while we take care of hosting the challenge, handling user submissions, and maintaining the leaderboard.

- **Evaluation inside environments**: EvalAI lets participants submit code for their agent in the form of docker images which are evaluated against test environments on the evaluation server. During evaluation, the worker fetches the image, test environment, and the model snapshot and spins up a new container to perform evaluation.

- **CLI support**: [evalai-cli](https://github.com/Cloud-CV/evalai-cli) is designed to extend the functionality of the EvalAI web application to your command line to make the platform more accessible and terminal-friendly.

- **Portability**: EvalAI is designed with keeping in mind scalability and portability of such a system from the very inception of the idea. Most of the components rely heavily on open-source technologies – Docker, Django, Node.js, and PostgreSQL.

- **Faster Evaluation**: We warm-up the worker nodes at start-up by importing the challenge code and pre-loading the dataset in memory. We also split the dataset into small chunks that are simultaneously evaluated on multiple cores. These simple tricks result in faster evaluation and reduces the evaluation time by an order of magnitude in some cases.

- **Easy Hosting**: Hosting a challenge is streamlined. One can create the challenge on EvalAI using the intuitive UI (work-in-progress) or using zip configuration file.

- **Centralized Leaderboard**: Challenge Organizers whether host their challenge on EvalAI or forked version of EvalAI, they can send the results to main EvalAI server. This helps to build a centralized platform to keep track of different challenges.

A question we’re often asked is: Doesn’t Kaggle already do this? The central differences are:

<p align="center"><img width="65%" src="docs/source/\_static/img/kaggle_comparison.png" /></p>

## Goal

Our ultimate goal is to build a centralized platform to host, participate and collaborate in AI challenges organized around the globe and we hope to help in benchmarking progress in AI.

## Performance comparison

Some background: The [Visual Question Answering Challenge (VQA) 2016](http://www.visualqa.org/vqa_v1_challenge.html) hosted on some other platform in 2016, took **~10 minutes** for evaluation of a submission. EvalAI hosted [VQA Challenge 2017](https://evalai.cloudcv.org/featured-challenges/1/overview) and [VQA Challenge 2018](https://evalai.cloudcv.org/web/challenges/challenge-page/80/overview) and the dataset for the [VQA Challenge 2017, 2018](http://www.visualqa.org/challenge.html) is twice as large. Despite this, we’ve found that our parallelized backend only takes **~130 seconds** to evaluate on the whole test set VQA 2.0 dataset.

## Installation instructions

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

## Citing EvalAI
If you are using EvalAI for hosting challenges, please cite the following technical report:

```
@article{EvalAI,
    title   =  {EvalAI: Towards Better Evaluation Systems for AI Agents},
    author  =  {Deshraj Yadav and Rishabh Jain and Harsh Agrawal and Prithvijit
                Chattopadhyay and Taranjeet Singh and Akash Jain and Shiv Baran
                Singh and Stefan Lee and Dhruv Batra},
    year    =  {2019},
    volume  =  arXiv:1902.03570
}
```
The arxiv paper is available [here](https://arxiv.org/abs/1902.03570).

## Team

EvalAI is currently maintained by [Deshraj Yadav](https://deshraj.github.io), [Rishabh Jain](https://rishabhjain2018.github.io/), [Akash Jain](http://www.jainakash.in/), [Taranjeet Singh](http://taranjeet.github.io/), and [Shiv Baran Singh](http://www.shivbaran.in/). A non-exhaustive list of other major contributors includes: [Harsh Agarwal](https://dexter1691.github.io/), [Prithvijit Chattopadhyay](https://prithv1.github.io/), [Devi Parikh](https://www.cc.gatech.edu/~parikh/) and [Dhruv Batra](https://www.cc.gatech.edu/~dbatra/).

## Contribution guidelines

If you are interested in contributing to EvalAI, follow our [contribution guidelines](https://github.com/Cloud-CV/EvalAI/blob/master/.github/CONTRIBUTING.md).
