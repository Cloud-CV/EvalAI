# Remote Evaluation
Each challenge has an evaluation script, which evaluates the submission of participants and returns the scores which will populate the leaderboard. The logic for evaluating and judging a submission is customizable and varies from challenge to challenge, but the overall structure of evaluation scripts is fixed due to architectural reasons.

## Writing Remote Evaluation Script

The starter template for remote challenge evaluation can be found [here](https://github.com/Cloud-CV/EvalAI-Starters/tree/master/remote_challenge_evaluation).

Here are the steps to configure remote evaluation:

1. **Setup Configs**:

    To configure authentication for the challenge set the following environment variables:

    1. AUTH_TOKEN:  Go to [profile page](https://eval.ai/web/profile) -> Click on `Get your Auth Token` -> Click on the Copy button. The auth token will get copied to your clipboard.
    2. API_SERVER: Use `https://eval.ai` when setting up challenge on production server. Otherwise, use `https://staging.eval.ai`
        <img src="_static/img/github_based_setup/evalai_profile_get_auth_token.png"><br />
        <img src="_static/img/github_based_setup/evalai_profile_copy_auth_token.png"><br />
    3. QUEUE_NAME: Go to the challenge manage tab to fetch the challenge queue name.
    4. CHALLENGE_PK: Go to the challenge manage tab to fetch the challenge primary key.
        <img src="_static/img/remote_evaluation_meta.png"><br />
    5. SAVE_DIR: (Optional) Path to submission data download location.

2. **Write `evaluate` method**:
    Evaluation scripts are required to have an `evaluate()` function. This is the main function, which is used by workers to evaluate the submission messages.

    The syntax of evaluate function for a remote challenge is:

    ```python
    def evaluate(user_submission_file, phase_codename, test_annotation_file = None, **kwargs)
        pass
    ```

    It receives three arguments, namely:

    - `user_annotation_file`: It represents the local path of the file submitted by the user for a particular challenge phase.

    - `phase_codename`: It is the `codename` of the challenge phase from the [challenge configuration yaml](https://github.com/Cloud-CV/EvalAI-Starters/blob/master/challenge_config.yaml). This is passed as an argument so that the script can take actions according to the challenge phase.

    - `test_annotation_file`: It represents the local path to the annotation file for the challenge. This is the file uploaded by the Challenge host while creating a challenge.

    You may pass the `test_annotation_file` as default argument or choose to pass separately in the `main.py` depending on the case. The `phase_codename` is passed automatically but is left as an argument to allow customization.

    After reading the files, some custom actions can be performed. This varies per challenge.

    The `evaluate()` method also accepts keyword arguments.

    **IMPORTANT** ⚠️: If the `evaluate()` method fails due to any reason or there is a problem with the submission, please ensure to raise an `Exception` with an appropriate message.
