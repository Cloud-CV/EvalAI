# Host Challenge
EvalAI supports hosting challenges with different configurations. Challenge organizers can choose to customize most aspects of the challenge but not limited to:

- Evaluation metrics
- Language/Framework to implement the metric
- Number of phases and data-splits
- Daily / monthly / overall submission limit
- Number of workers evaluating submissions
- Evaluation on remote machines
- Show / hide error bars on leaderboard
- Public / private leaderboards
- Allow / block certain email addresses to participate in the challenge or phase
- Choose which fields to export while downloading challenge submissions

We have hosted challenges from different domains such as:

- Machine learning ([2019 SIOP Machine Learning Competition](https://eval.ai/web/challenges/challenge-page/160/leaderboard/481))
- Deep learning ([Visual Dialog Challenge 2019 ](https://eval.ai/web/challenges/challenge-page/161/leaderboard/483))
- Computer vision ([Vision and Language Navigation](https://eval.ai/web/challenges/challenge-page/97/leaderboard/270))
- Natural language processing ([VQA Challenge 2019](https://eval.ai/web/challenges/challenge-page/163/leaderboard/498))
- Healthcare ([fastMRI Image Reconstruction ](https://eval.ai/web/challenges/challenge-page/153/leaderboard/447))
- Self-driving cars ([CARLA Autonomous Driving Challenge](https://eval.ai/web/challenges/challenge-page/246/leaderboard/817))

## Host challenge using github

### Step 1: Use template

Use [EvalAI-Starters](https://github.com/Cloud-CV/EvalAI-Starters) template. See [this](https://docs.github.com/en/free-pro-team@latest/github/creating-cloning-and-archiving-repositories/creating-a-repository-from-a-template) on how to use a repository as template.

   <img src="../../_static/img/github_based_setup/use_template_1.png"><br />
   <img src="../../_static/img/github_based_setup/use_template_2.png"><br />

### Step 2: Generate github token

Generate your [github personal access token](https://docs.github.com/en/free-pro-team@latest/github/authenticating-to-github/creating-a-personal-access-token) and copy it in clipboard.

Add the github personal access token in the forked repository's [secrets](https://docs.github.com/en/free-pro-team@latest/actions/reference/encrypted-secrets#creating-encrypted-secrets-for-a-repository) with the name `AUTH_TOKEN`.

### Step 3: Setup host configuration

Now, go to [EvalAI](https://eval.ai) to fetch the following details -
   1. `evalai_user_auth_token` - Go to [profile page](https://eval.ai/web/profile) after logging in and click on `Get your Auth Token` to copy your auth token.
   2. `host_team_pk` - Go to [host team page](https://eval.ai/web/challenge-host-teams) and copy the `ID` for the team you want to use for challenge creation.
   3. `evalai_host_url` - Use `https://eval.ai` for production server and `https://staging.eval.ai` for staging server.

   <img src="../../_static/img/github_based_setup/evalai_profile.png"><br />

### Step 4: Setup automated update push

Create a branch with name `challenge` in the forked repository from the `master` branch.
<span style="color:purple">Note: Only changes in `challenge` branch will be synchronized with challenge on EvalAI.</span>

Add `evalai_user_auth_token` and `host_team_pk` in `github/host_config.json`.
   <img src="../../_static/img/github_based_setup/host_config_json.png"><br />

### Step 5: Update challenge details

Read [EvalAI challenge creation documentation](https://evalai.readthedocs.io/en/latest/configuration.html) to know more about how you want to structure your challenge. Once you are ready, start making changes in the yaml file, HTML templates, evaluation script according to your need.

### Step 6: Push changes to the challenge

Commit the changes and push the `challenge` branch in the repository and wait for the build to complete. View the [logs of your build](https://docs.github.com/en/free-pro-team@latest/actions/managing-workflow-runs/using-workflow-run-logs#viewing-logs-to-diagnose-failures).
    <img src="../../_static/img/github_based_setup/commit.png"><br />
    <img src="../../_static/img/github_based_setup/build_logs.png"><br />

If challenge config contains errors then a `issue` will be opened automatically in the repository with the errors otherwise the challenge will be created on EvalAI.

### Step 7: Verify challenge

Go to [Hosted Challenges](https://eval.ai/web/hosted-challenges) to view your challenge. The challenge will be publicly available once EvalAI admin approves the challenge.

To update the challenge on EvalAI, make changes in the repository and push on `challenge` branch and wait for the build to complete.

## Host prediction upload based challenge

### Step 1: Setup challenge configuration

We have created a sample challenge configuration that we recommend you to use to get started. Use [EvalAI-Starters](https://github.com/Cloud-CV/EvalAI-Starters) template to start. See [this](https://docs.github.com/en/free-pro-team@latest/github/creating-cloning-and-archiving-repositories/creating-a-repository-from-a-template) on how to use a repository as template.

### Step 2: Edit challenge configuration

Open [`challenge_config.yml`](https://github.com/Cloud-CV/EvalAI-Starters/blob/master/challenge_config.yaml) from the repository that you cloned in step-1. This file defines all the different settings of your challenge such as start date, end date, number of phases, and submission limits etc.

Edit this file based on your requirement. For reference to the fields, refer to the <a href="../configuration/challenge-config.html">challenge configuration reference section</a>.

### Step 3: Edit evaluation script

Next step is to edit the challenge evaluation script that decides what metrics the submissions are going to be evaluated on for different phases.

Please refer to the <a href="../evaluation/evaluation-scripts.html#writing-an-evaluation-script">writing evaluation script</a> to complete this step.

### Step 4: Edit challenge HTML templates

Almost there. You just need to update the HTML templates in the `templates/` directory of the bundle that you cloned.

EvalAI supports all kinds of HTML tags which means you can add images, videos, tables etc. Moreover, you can add inline CSS to add custom styling to your challenge details.
<!-- 
### Step 5: Upload configuration on EvalAI

Finally run the `./run.sh` script in the bundle. It will generate a `challenge_config.zip` file that contains all the details related to the challenge. Now, visit [EvalAI - Host challenge page](https://eval.ai/web/challenge-host-teams) and select/create a challenge host team. Then upload the `challenge_config.zip`. -->

**Congratulations!** you have submitted your challenge configuration for review and [EvalAI team](https://eval.ai/team) has notified about this. [EvalAI team](https://eval.ai/team) will review and will approve the challenge.

If you have issues in creating a challenge on EvalAI, please feel free to contact us at [team@eval.ai](mailto:team@eval.ai) create an issue on our [GitHub issues page](https://github.com/Cloud-CV/EvalAI/issues/new).

## Host a remote evaluation challenge

### Step 1: Set up the challenge

Follow <a href="host-challenge.html#host-challenge-using-github">host challenge using github section</a> to set up a challenge on EvalAI.

### Step 2: Edit challenge configuration

Set the `remote_evaluation` parameter to `True` in [`challenge_config.yaml`](https://github.com/Cloud-CV/EvalAI-Starters/blob/621f0cb37b2f1951613c9b6c967ce35be55d34c8/challenge_config.yaml#L12). This challenge config file defines all the different settings of your challenge such as start date, end date, number of phases, and submission limits etc.

Edit this file based on your requirement. For reference to the fields, refer to the <a href="../configuration/challenge-config.html">challenge configuration reference section</a>.

Please ensure the following fields are set to the following values:

- `remote_evaluation : True`

Refer to the [following documentation](https://evalai.readthedocs.io/en/latest/configuration.html) for details on challenge configuration.

### Step 3: Edit remote evaluation script

Next step is to edit the challenge evaluation script that decides what metrics the submissions are going to be evaluated on for different phases.
Please refer to <a href="../evaluation/remote-evaluation.html#writing-remote-evaluation-script">Writing Remote Evaluation Script</a> section to complete this step.

### Step 4: Set up remote evaluation worker

1. Create conda environment to run the evaluation worker. Refer to [conda's create environment section](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#creating-an-environment-with-commands) to set up a virtual environment.
2. Install the worker requirements from the `EvalAI-Starters/remote_challenge_evaluation` present [here](https://github.com/Cloud-CV/EvalAI-Starters/blob/master/remote_challenge_evaluation/requirements.txt):

   ```sh
   cd EvalAI-Starters/
   pip install remote_challenge_evaluation/requirements.txt

   ```

3. Start evaluation worker:

   ```sh
   cd EvalAI-Starters/remote_challenge_evaluation
   python main.py
   ```

If you have issues in creating a challenge on EvalAI, please feel free to contact us at [team@eval.ai](mailto:team@eval.ai) create an issue on our [GitHub issues page](https://github.com/Cloud-CV/EvalAI/issues/new).

[evalai-starters]: https://github.com/Cloud-CV/EvalAI-Starters
[evalai-cli]: https://cli.eval.ai/
[evalai]: http://eval.ai
[docker-compose]: https://docs.docker.com/compose/install/
[docker]: https://docs.docker.com/install/linux/docker-ce/ubuntu/
