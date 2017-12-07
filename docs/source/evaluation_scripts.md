## Evaluation Script

Each challenge has an evaluation script, which evaluates the submission of participants and returns the scores which populates its leaderboard.

The logic for evaluating and judging a submission is custom and varies from challenge to challenge. But the overall structure of evaluation script is fixed due to architectural reasons.

It is mandatory for evaluation script to write a `evaluate` function. This is kind of a main function, which is used by worker to evaluate any submission message.

The syntax of evaluate function is

```

def evaluate(test_annotation_file, user_annotation_file, phase_codename):

    pass

```

It receives three arguments, namely:

* test_annotation_file

It is the path of the annotation file for a challenge. This is the file uploaded by Challenge Host while creating a Challenge.

* user_annotation_file

It is the path of the file submitted by the user for a particular phase.

* phase_codename

It is the code name of the `ChallengePhase` model. This is passed as argument, so that the script can take action according to the phase.

After reading the files, some custom action can be performed. This varies per challenge.

After all the processing is done, this scripts sends an output, which is used to populate the leaderboard. The output should be in the following format

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

`output` should contain a key named `result` which is a list containing entries per challenge phase split. Each challenge phase split object contains various keys, which are then displayed as columns in leaderboard.
