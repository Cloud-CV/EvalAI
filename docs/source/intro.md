# Introduction

[EvalAI] aims to build a centralized platform to host, participate, and collaborate in Artificial Intelligence (AI) challenges organized around the globe and hope to help in benchmarking progress in AI.

<img src="/_static/img/teaser.png">

## Features

### Custom evaluation protocol

We allow creation of an arbitrary number of evaluation phases and dataset splits, compatibility using any programming language, and organizing results in both public and private leaderboards.

### Remote evaluation

Certain large-scale challenges need special compute capabilities for evaluation. If the challenge needs extra computational power, challenge organizers can easily add their own cluster of worker nodes to process participant submissions while we take care of hosting the challenge, handling user submissions, and maintaining the leaderboard.

### Evaluation inside RL environments

[EvalAI] lets participants submit code for their agent in the form of docker images which are evaluated against test environments on the evaluation server. During evaluation, the worker fetches the image, test environment, and the model snapshot and spins up a new container to perform evaluation.

### CLI support

[EvalAI-CLI] is designed to extend the functionality of the [EvalAI] web application to your command line to make the platform more accessible and terminal-friendly.

### Portability

[EvalAI] was designed with keeping in mind scalability and portability of such a system from the very inception of the idea. Most of the components rely heavily on open-source technologies – Docker, Django, Node.js, and PostgreSQL.

### Faster evaluation

We warm-up the worker nodes at start-up by importing the challenge code and pre-loading the dataset in memory. We also split the dataset into small chunks that are simultaneously evaluated on multiple cores. These simple tricks result in faster evaluation and reduces the evaluation time by an order of magnitude in some cases.

[evalai-cli]: http://evalai-cli.cloudcv.org
[evalai]: http://evalai.cloudcv.org
