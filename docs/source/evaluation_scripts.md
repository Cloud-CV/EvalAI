## Writing Evaluation Script

Each challenge has an evaluation script, which evaluates the submission of participants and returns the scores which will populate the leaderboard.

The logic for evaluating and judging a submission is customizable and varies from challenge to challenge, but the overall structure of evaluation scripts are fixed due to architectural reasons.

Evaluation scripts are required to have an `evaluate` function. This is the main function, which is used by workers to evaluate the submission messages.

The syntax of evaluate function is:

```

def evaluate(test_annotation_file, user_annotation_file, phase_codename, **kwargs):

    pass

```

It receives three arguments, namely:

* test_annotation_file

This is the path to the annotation file for the challenge. This is the file uploaded by the Challenge Host while creating a Challenge.

* user_annotation_file

This is the path of the file submitted by the user for a particular phase.

* phase_codename

This is the `ChallengePhase` model codename. This is passed as an argument, so that the script can take actions according to the phase.

After reading the files, some custom actions can be performed. This varies per challenge.

The `evaluate()` method also accepts keyword arguments. By default, we provide you metadata of each submission to your challenge which you can use to send notifications to your slack channel or to some other webhook service. Following is an example code showing how to get the submission metadata in your evaluation script and send a slack notification if the accuracy is more than some value `X` (X being 90 in the expample given below). 

```
def evaluate(test_annotation_file, user_annotation_file, phase_codename, **kwargs):

    submission_metadata = kwargs.get("submission_metadata")
    print submission_metadata

    # Do stuff here
    # Let's set `score` to 90 as an example

    score = 91
    if score > 90:
        slack_data = kwargs.get("submission_metadata")
        webhook_url = "Your Slack Webhook URL comes here"
        # To know more about slack webhook, checkout this link: https://api.slack.com/incoming-webhooks

        response = requests.post(
            webhook_url,
            data=json.dumps({'text': "*Flag raised for submission:* \n \n" + str(slack_data)}),
            headers={'Content-Type': 'application/json'})

    # Do more stuff here
```

The above example can be modified and used to find if some participant team is cheating or not. There are many more ways for which you can use this metadata.

After all the processing is done, this script will send an output, which is used to populate the leaderboard. The output should be in the following format:


```

output = {}
output['result'] = [
    {
        'dataset_split_1: {
            'score': score,
        }
    },
    {
        'dataset_split_2': {
            'score': score,
        }
    }
]
return output

```

`output` should contain a key named `result`, which is a list containing entries per dataset split that is available for the challenge phase under consideration (In the function definition of `evaluate` shown above, the argument: `phase_codename` will receive the _codename_ for the challenge phase against which the submission was made). Each entry in the list should be an object that has a key with the corresponding dataset split codename(`dataset_split_1` and `dataset_split_2` for this example). Each of these dataset split objects contains various keys (`score` in this example), which are then displayed as columns in the leaderboard. 

> NOTE: `dataset_split_1` and `dataset_split_2` are codenames for dataset splits that should be evaluated with each submission for the challenge phase obtained via *phase_codename*. 

**Note**: If your evaluation script uses some precompiled libraries (<a href="https://github.com/pdollar/coco/">MSCOCO</a> for example), then make sure that the library is compiled against a Linux Distro (Ubuntu 14.04 recommended). Libraries compiled against OSx or Windows might or might not work properly.
