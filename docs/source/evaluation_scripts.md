## Writing Evaluation Script

### Writing an evaluation script

Each challenge has an evaluation script, which evaluates the submission of participants and returns the scores which will populate the leaderboard. The logic for evaluating and judging a submission is customizable and varies from challenge to challenge, but the overall structure of evaluation scripts are fixed due to architectural reasons.

Evaluation scripts are required to have an `evaluate()` function. This is the main function, which is used by workers to evaluate the submission messages.

The syntax of evaluate function is:

```
def evaluate(test_annotation_file, user_annotation_file, phase_codename, **kwargs):
    pass
```

It receives three arguments, namely:

- `test_annotation_file`: It represents the local path to the annotation file for the challenge. This is the file uploaded by the Challenge host while creating a challenge.

- `user_annotation_file`: It represents the local path of the file submitted by the user for a particular challenge phase.

- `phase_codename`: It is the `codename` of the challenge phase from the [challenge configuration yaml](https://github.com/Cloud-CV/EvalAI-Starters/blob/master/challenge_config.yaml). This is passed as an argument so that the script can take actions according to the challenge phase.

After reading the files, some custom actions can be performed. This varies per challenge.

The `evaluate()` method also accepts keyword arguments. By default, we provide you metadata of each submission to your challenge which you can use to send notifications to your slack channel or to some other webhook service. Following is an example code showing how to get the submission metadata in your evaluation script and send a slack notification if the accuracy is more than some value `X` (X being 90 in the example given below).

```
def evaluate(test_annotation_file, user_annotation_file, phase_codename, **kwargs):

    submission_metadata = kwargs.get("submission_metadata")
    print submission_metadata

    # Do stuff here
    # Set `score` to 91 as an example

    score = 91
    if score > 90:
        slack_data = kwargs.get("submission_metadata")
        webhook_url = "Your slack webhook url comes here"
        # To know more about slack webhook, checkout this link: https://api.slack.com/incoming-webhooks

        response = requests.post(
            webhook_url,
            data=json.dumps({'text': "*Flag raised for submission:* \n \n" + str(slack_data)}),
            headers={'Content-Type': 'application/json'})

    # Do more stuff here
```

The above example can be modified and used to find if some participant team is cheating or not. There are many more ways for which you can use this metadata.

After all the processing is done, this `evaluate()` should return an output, which is used to populate the leaderboard. The output should be in the following format:

```
output = {}
output['result'] = [
            {
                'train_split': {
                    'Metric1': 123,
                    'Metric2': 123,
                    'Metric3': 123,
                    'Total': 123,
                }
            },
            {
                'test_split': {
                    'Metric1': 123,
                    'Metric2': 123,
                    'Metric3': 123,
                    'Total': 123,
                }
            }
        ]

return output

```

Let's break down what is happening in the above code snippet.

1. `output` should contain a key named `result`, which is a list containing entries per dataset split that is available for the challenge phase in consideration (in the function definition of `evaluate()` shown above, the argument: `phase_codename` will receive the _codename_ for the challenge phase against which the submission was made).
2. Each entry in the list should be a dict that has a key with the corresponding dataset split codename (`train_split` and `test_split` for this example).
3. Each of these dataset split dict contains various keys (`Metric1`, `Metric2`, `Metric3`, `Total` in this example), which are then displayed as columns in the leaderboard.

### Writing a remote evaluation script

Just like a regular evaluation script, a remote evaluation script allows you to customize evaluation for your remote challenge. The starter template for remote challenge evaluation can be found [here](https://github.com/Cloud-CV/EvalAI-Starters/blob/master/remote_challenge_evaluation/evaluation_script_starter.py).

There are a few things that you need to configure:

1. **Set variables in the `__init__` method**: There are few variables that you need to set according to your challenge. The `auth_token` is fetched from the profile and `evalai_api_server` is set according to the server. The `challenge_pk` and `queue_name` can be fetched from the `Manage` tab of your challenge once it is up on  the server.

    Changing the `save_dir` is optional and up to your preference.

    ```python
    self.auth_token = ""  # Go to EvalAI UI to fetch your auth token
    self.evalai_api_server = ""  # For staging server, use -- https://staging.eval.ai; For production server, use -- https://eval.ai
    self.queue_name = ""  # Check Manage Tab of challenge for queue name
    self.challenge_pk = ""  # Check Manage Tab of challenge for challenge PK

    self.save_dir = "./" # Location where submissions are downloaded
    ```

2. **Edit the `evaluate` method**: Like a regular evaluation, the `evaluate` method in `RemoteEvaluationUtil` is similar. It includes the three arguments - `user_annotation_file`, `phase_codename`, `test_annotation_file`.

    Apart from that, we also pass `challenge_pk`, `phase_pk`, `submission_pk`, which only need to be used when updating the submission status on EvalAI.

    The syntax of evaluate function is:

    ```python
    def evaluate(test_annotation_file, challenge_pk, phase_pk, submission_pk, user_submission_file=None, phase_codename=None, **kwargs):
        pass
    ```

    Pass the `test_annotation_file` as default argument or choose to pass separately in the `main.py` depending on the case. The `phase_codename` is passed automatically but is left as as argument for customization.

There are two possible cases when you run your evaluation:

1. Evaluation is successful: When this happens, use the `update_finished` class method to pass in the metrics and set the status to `finished` for this submission.

    The `result` should be structed in the same way as regular evaluation as shown in the previous section.

    You can also pass optional `metadata` and other files to help participants understand the `stdout` and `stderr` if needed.

    The syntax is as follows:

    ``` python
    self.update_finished(
        evalai,
        phase_pk,
        submission_pk,
        result='[{"split": "<split-name>", "show_to_participant": true,"accuracies": {"Metric1": 80,"Metric2": 60,"Metric3": 60,"Total": 10}}]'
    )
    ```

2. Evaluation fails: There might be cases where there are errors in the evaluation. In this case it is important to show the error to the participants and update the submission status to `failed`. This can be done using the `update_failed` method.

    The syntax is shown below:

    ```python
    self.update_failed(
        phase_pk,
        submission_pk,
        submission_error,
        ...
    )
    ```
