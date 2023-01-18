## Writing Evaluation Script

### Writing an Evaluation Script

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

### Writing Remote Evaluation Script

Each challenge has an evaluation script, which evaluates the submission of participants and returns the scores which will populate the leaderboard. The logic for evaluating and judging a submission is customizable and varies from challenge to challenge, but the overall structure of evaluation scripts is fixed due to architectural reasons.

The starter template for remote challenge evaluation can be found [here](https://github.com/Cloud-CV/EvalAI-Starters/blob/master/remote_challenge_evaluation/evaluation_script_starter.py).

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

### Writing Code Upload Challenge Evaluation

Each challenge has an evaluation script, which evaluates the submission of participants and returns the scores which will populate the leaderboard. The logic for evaluating and judging a submission is customizable and varies from challenge to challenge, but the overall structure of evaluation scripts is fixed due to architectural reasons.

In code-upload challenges, the evaluation is tighly-coupled with the agent and environment containers: The agent container continuously interacts with the environment container, and the environment container provides feedback to the agent until the environment provides a `stop` signal when the goal is reached or when the agent cannot continue further. Therefore, it is important to describe the interaction between the containers, how once can set up the individual containers, and how can the evaluation be performed.

The starter templates for code-upload challenge evaluation can be found [here](https://github.com/Cloud-CV/EvalAI-Starters/tree/master/code_upload_challenge_evaluation). Here, we have a code organization to facilitate communication between the agent and environment.

Here are the steps to configure evaluation for code upload challenges:

1. **Create an environment**:
    There are few steps involved in creating an environment:
    1. *Edit the evaluator_environment*: This class defines the environment which can be like a [gym environment](https://www.gymlibrary.dev/content/environment_creation/) or a [habitat environment](https://github.com/facebookresearch/habitat-lab/blob/b1f2d4791a0065d0791001b72a6c96748a5f9ae0/habitat-lab/habitat/core/env.py) and other related attributes and method. Modify the `evaluator_environment` containing a gym environment shown [here](https://github.com/Cloud-CV/EvalAI-Starters/blob/8338085c6335487332f5b57cf7182201b8499aad/code_upload_challenge_evaluation/environment/environment.py#L21-L32):

        ```python
        class evaluator_environment:
            def __init__(self, environment="CartPole-v0"):
                self.score = 0
                self.feedback = None
                self.env = gym.make(environment)
                self.env.reset()

            def get_action_space(self):
                return list(range(self.env.action_space.n))

            def next_score(self):
                self.score += 1
        ```

        The attribute `self.env` here is the environment, `self.feedback` is the observations from the sensors of the agent after performing an action and `self.score` stores the score at each step.

        The `next_score` method shows how the score can be updated and shown towards the end of the evaluation and the `get_action_space` gets the list of possible actions. You can add custom methods and attributes which help in interaction with the environment.

    2. _Edit the Environment service_: This service is hosted on the GRPC server in order to get actions in form of messages from the agent container. Modify the lines shown [here](https://github.com/Cloud-CV/EvalAI-Starters/blob/8338085c6335487332f5b57cf7182201b8499aad/code_upload_challenge_evaluation/environment/environment.py#L35-L65):

        ```python
        class Environment(evaluation_pb2_grpc.EnvironmentServicer):
            def __init__(self, challenge_pk, phase_pk, submission_pk, server):
                self.challenge_pk = challenge_pk
                self.phase_pk = phase_pk
                self.submission_pk = submission_pk
                self.server = server

            def get_action_space(self, request, context):
                message = pack_for_grpc(env.get_action_space())
                return evaluation_pb2.Package(SerializedEntity=message)

            def act_on_environment(self, request, context):
                global EVALUATION_COMPLETED
                if not env.feedback or not env.feedback[2]:
                    action = unpack_for_grpc(request.SerializedEntity)
                    env.next_score()
                    env.feedback = env.env.step(action)
                if env.feedback[2]:
                    if not LOCAL_EVALUATION:
                        update_submission_result(
                            env, self.challenge_pk, self.phase_pk, self.submission_pk
                        )
                    else:
                        print("Final Score: {0}".format(env.score))
                        print("Stopping Evaluation!")
                        EVALUATION_COMPLETED = True
                return evaluation_pb2.Package(
                    SerializedEntity=pack_for_grpc(
                        {"feedback": env.feedback, "current_score": env.score,}
                    )
                )
        ```

        You can modify the relevant parts of the environment service in order to make it work for your case. For example, `feedback` can totally depend on the results obtained from the `env.env` after performing an action, which in-turn depends on the sensors expected from the agent. In our example, `feedback[2]` is the stop signal sensor. The `unpack_for_grpc` and `pack_for_grpc` are methods to receive and send messages with the agent.

        This is a high-level description of the class and the implementations may vary on a case-by-case basis.
    3. _Edit the requirements file_: Change the [requirements file](https://github.com/Cloud-CV/EvalAI-Starters/blob/master/code_upload_challenge_evaluation/requirements/environment.txt) according to the packages required by your environment.

    4. _Edit environment Dockerfile_: You may choose to modify the [Dockerfile](https://github.com/Cloud-CV/EvalAI-Starters/blob/master/code_upload_challenge_evaluation/docker/environment/Dockerfile) which will host the Environment service on a GRPC server.

    5. _Edit the docker environment variables_: Fill in the following information in the [`docker.env`](https://github.com/Cloud-CV/EvalAI-Starters/blob/master/code_upload_challenge_evaluation/docker/environment/docker.env) file:

        ```env
        AUTH_TOKEN=<Add your EvalAI Auth Token here>
        EVALAI_API_SERVER=<https://eval.ai>
        LOCAL_EVALUATION = True
        QUEUE_NAME=<Go to the challenge manage tab to get challenge queue name.>
        ```

    6. _Create the docker image and host it_: Create an environment docker image using the above steps using `docker build` command and host it.

    7. _Add environment image the challenge configuration for challenge phase_: For each challenge phase, add the link to the environment image in the [challenge configuration](https://evalai.readthedocs.io/en/latest/configuration.html):

        ```yaml
        ...
        challenge_phases:
            - id: 1
            ...
            - environment_image: <docker image uri>
        ...
        ```

    Example References:
    - [Habitat Benchmark](https://github.com/facebookresearch/habitat-lab/blob/b1f2d4791a0065d0791001b72a6c96748a5f9ae0/habitat-lab/habitat/core/benchmark.py): This file contains description of an evaluation class which evaluates agents on the environment.
    - 

2. **Create a dummy agent**:
    The participants are expected to submit docker images for their agents which will contain the policy/network and the methods to interact with the environment.

    Like environment, there are a few steps involved in creating the agent:
    1. _Create a dummy agent script_: In order to help the participants understand what your environment expects, please create a python script for a dummy/baseline/random agent and submit the agent to your challenge/environment for evaluation.

        The `agent.py` file should contain a description of the agent, the methods that the environment expects the agent to have.

        An example agent taken from [Habitat Rearrangement Challenge 2022](https://github.com/facebookresearch/habitat-challenge/blob/rearrangement-challenge-2022/agents/random_agent.py) that randomly picks actions given observations is shown below.

        ```python
        class RandomAgent(habitat.Agent):
            def __init__(self, task_config: habitat.Config):
                self._POSSIBLE_ACTIONS = task_config.TASK.POSSIBLE_ACTIONS

            def reset(self):
                pass

            def act(self, observations):
                return {
                    "action": ("ARM_ACTION", "BASE_VELOCITY", "REARRANGE_STOP"),
                    "action_args": {
                        "arm_action": np.random.rand(7),
                        "grip_action": np.random.rand(1),
                        "base_vel": np.random.rand(2),
                        "REARRANGE_STOP": np.random.rand(1),
                    },
                }
        ```

        Note that this example is specific to superclass `habitat.Agent` and the corresponding environment is `habitat-lab`'s [`Challenge`](https://github.com/facebookresearch/habitat-lab/blob/b1f2d4791a0065d0791001b72a6c96748a5f9ae0/habitat-lab/habitat/core/challenge.py#L9) which makes the agent perform actions on the environment using the `reset` and `act` methods.

        The `agent.py` should also contain a `main()` function which either submits the agent or the action to the environment.

        We provide a template for `agent.py` [here](https://github.com/Cloud-CV/EvalAI-Starters/blob/master/code_upload_challenge_evaluation/agent/agent.py):

        ```python
        import evaluation_pb2
        import evaluation_pb2_grpc
        import grpc
        import os
        import pickle
        import time

        time.sleep(30)

        LOCAL_EVALUATION = os.environ.get("LOCAL_EVALUATION")

        if LOCAL_EVALUATION:
            channel = grpc.insecure_channel("environment:8085")
        else:
            channel = grpc.insecure_channel("localhost:8085")

        stub = evaluation_pb2_grpc.EnvironmentStub(channel)

        def pack_for_grpc(entity):
            return pickle.dumps(entity)

        def unpack_for_grpc(entity):
            return pickle.loads(entity)

        flag = None

        while not flag:
            base = unpack_for_grpc(
                stub.act_on_environment(
                    evaluation_pb2.Package(SerializedEntity=pack_for_grpc(1))
                ).SerializedEntity
            )
            flag = base["feedback"][2]
            print("Agent Feedback", base["feedback"])
            print("*"* 100)

        ```

        This is a very basic example where the the agent sends action (`1`) to the environment and the environment sends back feedback after acting on the environment with the sent action.

        The feedback is checked for stop signal, and usually contains observations from the sensors. The action then can depend on the `feedback` from the environment.

    2. _Edit the requirements file_: Change the [requirements file](https://github.com/Cloud-CV/EvalAI-Starters/blob/master/code_upload_challenge_evaluation/requirements/agent.txt) according to the packages required by an agent.

    3. _Edit environment Dockerfile_: You may choose to modify the [Dockerfile](https://github.com/Cloud-CV/EvalAI-Starters/blob/master/code_upload_challenge_evaluation/docker/agent/Dockerfile) which will run the `agent.py` file and interact with environment.

    4. _Edit the docker environment variables_: Fill in the following information in the [`docker.env`](https://github.com/Cloud-CV/EvalAI-Starters/blob/master/code_upload_challenge_evaluation/docker/agent/docker.env) file:

        ```env
        LOCAL_EVALUATION = True
        ```

    Example References:
    - [Habitat Rearrangement Challenge 2022 - Random Agent](https://github.com/facebookresearch/habitat-challenge/blob/rearrangement-challenge-2022/agents/random_agent.py): This is an example of a dummy agent created for the [Habitat Rearrangement Challenge 2022](https://eval.ai/web/challenges/challenge-page/1820/overview) which is then sent to the evaluator (here, [Habitat Benchmark](https://github.com/facebookresearch/habitat-lab/blob/b1f2d4791a0065d0791001b72a6c96748a5f9ae0/habitat-lab/habitat/core/benchmark.py)) for evaluation.

### Writing Static Code Upload Challenge Evaluation Script

The starter templates for static code-upload challenge evaluation can be found [here](https://github.com/Cloud-CV/EvalAI-Starters/evaluation_script/main.py). Note that the evaluation file provided will be used on our submission workers, just like prediction upload challenges.

See [writing an evaluation script] section (evaluation_scripts.html#writing-an-evaluation-script) in order to write evaluation scripts for these types of challenges.

A good example of a well-documented evaluation script for static code-upload challenges is [My Seizure Gauge Forecasting Challenge 2022](https://github.com/seermedical/msg-2022).
