# Host challenge

EvalAI supports hosting challenges with different configurations. Challenge organizers can choose to customize most aspects of the challenge but not limited to:

- Evalutaion metrics
- Language/Framework to implement the metric
- Number of phases and data-splits
- Daily / monthly / overall submission limit
- Number of workers evaluating submissions
- Evaluation on remote machines
- Provide your AWS credentials to host code upload based challenge
- Show / hide error bars on leaderboard
- Public / private leaderboards
- Allow / block certain email addresses to participate in the challenge or phase
- Choose which fields to export while downloading challenge submissions

We have hosted challenges from different domains such as:

- Machine learning ([2019 SIOP Machine Learning Competition](https://evalai.cloudcv.org/web/challenges/challenge-page/160/leaderboard/481))
- Deep learning ([Visual Dialog Challenge 2019 ](https://evalai.cloudcv.org/web/challenges/challenge-page/161/leaderboard/483))
- Computer vision ([Vision and Language Navigation](https://evalai.cloudcv.org/web/challenges/challenge-page/97/leaderboard/270))
- Natural language processing ([VQA Challenge 2019](https://evalai.cloudcv.org/web/challenges/challenge-page/163/leaderboard/498))
- Healthcare ([fastMRI Image Reconstruction ](https://evalai.cloudcv.org/web/challenges/challenge-page/153/leaderboard/447))
- Self-driving cars ([CARLA Autonomous Driving Challenge](https://evalai.cloudcv.org/web/challenges/challenge-page/246/leaderboard/817))

We categorize the challenges in two categories:

1. **Prediction upload based challenges**: Participants upload predictions corresponding to ground truth labels in the form of a file (could be any format: `json`, `npy`, `csv`, `txt` etc).

   Some of the popular prediction upload based challenges that we have hosted are shown below:

   <a href="https://evalai.cloudcv.org/web/challenges/list" target="_blank"><img src="_static/img/prediction-upload-challenges.png"></a><br />

   If you are interested in hosting prediction upload based challenges, then [click here](/host_challenge.html#host-prediction-upload-based-challenge).

    <br />

2. **Code upload based challenges**: In these kind of challenges, participants upload their training code in the form of docker images using [EvalAI-CLI].

   Some of the popular code upload based challenges that we have hosted are shown below:

   <a href="https://evalai.cloudcv.org/web/challenges/list" target="_blank"><img src="_static/img/code-upload-challenges.png"></a>

   If you are interested in hosting code upload based challenges, then [click here](/host_challenge.html#host-prediction-upload-based-challenge).

## Host Prediction upload based challenge

### Step 1: Setup challenge configuration

We have created a sample challenge configuration that we recommend you to use to get started. Fork and clone [EvalAI-Starters] repository to start.

### Step 2: Edit challenge configuration

Open [`challenge_config.yml`](https://github.com/Cloud-CV/EvalAI-Starters/blob/master/challenge_config.yaml) from the repository that you cloned in step-1. This file defines all the different settings of your challenge such as start date, end date, number of phases, and submission limits etc.

Edit this file based on your requirement. For reference to the fields, refer to the [challenge configuration reference section](/configuration.html#challenge-configuration).

### Step 3: Edit evaluation script

Next step is to edit the challenge evaluation script that decides what metrics the submissions are going to be evaluated on for different phases.

Please refer to the [writing evaluation script](evaluation_scripts.html) to complete this step.

### Step 4: Edit challenge HTML templates

Almost there. You just need to update the HTML templates in the `templates/` directory of the bundle that you cloned.

EvalAI supports all kinds of HTML tags which means you can add images, videos, tables etc. Moreover, you can add inline CSS to add custom styling to your challenge details.

### Step 5: Upload configuration on EvalAI

Finally run the `./run.sh` script in the bundle. It will generate a `challenge_config.zip` file that contains all the details related to the challenge. Now, vist [EvalAI - Host challenge page](https://evalai.cloudcv.org/web/challenge-host-teams) and select/create a challenge host team. Then upload the `challenge_config.zip`.

**Congratulations!** you have submitted your challenge configuration for review and [EvalAI team](https://evalai.cloudcv.org/team) has notified about this. [EvalAI team](https://evalai.cloudcv.org/team) will review and will approve the challenge.

If you have issues in creating a challenge on EvalAI, please feel free to contact us at [team@cloudcv.org](mailto:team@cloudcv.org) create an issue on our [Github issues page](https://github.com/Cloud-CV/EvalAI/issues/new).

## Host Code upload based challenge

### Step 1: Setup challenge configuration

Steps to create a Code upload based challenge is very similar to what it takes to create a [prediction upload based challenge](/host_challenge.html#host-a-prediction-upload-based-challenge).

We have created a sample challenge configuration that we recommend you to use to get started. Fork and clone [EvalAI-Starters] repository to start.

### Step 2: Edit challenge configuration

Open [`challenge_config.yml`](https://github.com/Cloud-CV/EvalAI-Starters/blob/master/challenge_config.yaml) from the repository that you cloned in step-1. This file defines all the different settings of your challenge such as start date, end date, number of phases, and submission limits etc. Edit this file based on your requirement.

Make sure that following fields are set correctly:

- `remote_evaluation` is set to `True`
- `is_docker_based` is set to `True`

For reference to the fields, refer to the [challenge configuration reference section](/configuration.html#challenge-configuration).

### Step 3: Edit evaluation script

Next step is to edit the challenge evaluation script that decides what metrics the submissions are going to be evaluated on for different phases.

Please refer to the [writing evaluation script](evaluation_scripts.html) to complete this step.

### Step 4: Edit challenge HTML templates

Almost there. You just need to update the HTML templates in the `templates/` directory of the bundle that you cloned.

EvalAI supports all kinds of HTML tags which means you can add images, videos, tables etc. Moreover, you can add inline CSS to add custom styling to your challenge details.

### Step 5: Upload configuration on EvalAI

Finally run the `./run.sh` script in the bundle. It will generate a `challenge_config.zip` file that contains all the details related to the challenge. Now, vist [EvalAI - Host challenge page](https://evalai.cloudcv.org/web/challenge-host-teams) and select/create a challenge host team. Then upload the `challenge_config.zip`.

**Congratulations!** you have submitted your challenge configuration for review and [EvalAI team](https://evalai.cloudcv.org/team) has notified about this. [EvalAI team](https://evalai.cloudcv.org/team) will review and will approve the challenge.

If you have issues in creating a challenge on EvalAI, please feel free to contact us at [team@cloudcv.org](mailto:team@cloudcv.org) create an issue on our [Github issues page](https://github.com/Cloud-CV/EvalAI/issues/new).

[evalai-starters]: https://github.com/cloud-CV/evalai-starters
[evalai-cli]: http://evalai-cli.cloudcv.org
[evalai]: http://evalai.cloudcv.org
[docker-compose]: https://docs.docker.com/compose/install/
[docker]: https://docs.docker.com/install/linux/docker-ce/ubuntu/
