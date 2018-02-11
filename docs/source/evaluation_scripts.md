## Writing Evaluation Script

Each challenge has an evaluation script, which evaluates the submission of participants and returns the scores which will populate the leaderboard.

The logic for evaluating and judging a submission is customizable and varies from challenge to challenge, but the overall structure of evaluation scripts are fixed due to architectural reasons.

Evaluation scripts are required to have an `evaluate` function. This is the main function, which is used by workers to evaluate the submission messages.

The syntax of evaluate function is:

```

def evaluate(test_annotation_file, user_annotation_file, phase_codename):

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

After all the processing is done, this script will send an output, which is used to populate the leaderboard. The output should be in the following format:

```

output = {}
output['result'] = [
    {
        'challege_phase_split_1': {
            'score': score,
        }
    },
    {
        'challege_phase_split_2': {
            'score': score,
        }
    }
]

```

`output` should contain a key named `result`, which is a list containing entries per challenge phase split. Each challenge phase split object contains various keys, which are then displayed as columns in leaderboard.

**Note**: If your evaluation script uses some precompiled libraries (<a href="https://github.com/pdollar/coco/">MSCOCO</a> for example), then make sure that the library is compiled against a Linux Distro (Ubuntu 14.04 recommended). Libraries compiled against OSx or Windows might or might not work properly.
