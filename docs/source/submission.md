## Submission

### How is a submission processed?

We are using REST APIs along with Queue based architecture to process submissions. When a participant makes a submission for a challenge, a REST API with url pattern `jobs:challenge_submission` is called. This API does the task of creating a new entry for submission model and then publishes a message to exchange `evalai_submissions` with a routing key of `submission.*.*`.

     User makes   --> API  --> Publish  --> RabbitMQ  --> Queue  --> Submission
    a submission               message      Exchange                  worker(s)


Exchange receives the message and then routes it to the queue `submission_task_queue`. At the end of `submission_task_queue` are workers (scripts/workers/submission_worker.py) which processes the submission message.

The worker can be run with

```
# assuming the current working directory is where manage.py lives
python scripts/workers/submission_worker.py
```

### How does submission worker function?

Submission worker is a python script which mostly runs as a daemon on a production server and simply acts as a python process in a development environment. To run submission worker in a development environment:

```
python scripts/workers/submission_worker.py
```

Before a worker fully starts, it does the following actions:

* Creates a new temporary directory for storing all its data files.

* Fetches the list of active challenges from the database. Active challenges are published challenges whose start date is less than present time and end date greater than present time. It loads all the challenge evaluation scripts in a variable called `EVALUATION_SCRIPTS`, with the challenge id as its key. The maps looks like this:

    ```
    EVALUATION_SCRIPTS = {
        <challenge_pk> : <evalutaion_script_loaded_as_module>,
        ....
    }
    ```

* Creates a connection with RabbitMQ by using the connection parameters specified in `settings.RABBITMQ_PARAMETERS`.

* After the connection is successfully created, creates an exchange with the name `evalai_submissions`
and two queues, one for processing submission message namely `submission_task_queue`, and other for getting add challenge message.

* `submission_task_queue` is then bound with the routing key of `submission.*.*` and add challenge message queue is bound with a key of `challenge.add.*`
Whenever a queue is bound to a exchange with any key, it will route the message to the corresponding queue as soon as the exchange receives a message with a key.

* Binding to any queue is also accompanied with a callback which basically takes a function as an argument. This function specifies what should be done when the queue receives a message.

e.g. `submission_task_queue` is using `process_submission_callback` as a function, which means that when a message is received in the queue, `process_submission_callback` will be called with the message passed as an argument.

Expressing it informally it will be something like

> _Queue_: Hey _Exchange_, I am `submission_task_queue`. I will be listening to messages from you on binding key of `submission.*.*`

> _Exchange_: Hey _Queue_, Sure! When I receive a message with a routing key of `submission.*.*`, I will give it to you

> _Queue_: Thanks a lot.

> _Queue_: Hey _Worker_, Just for the record, when I receive a new message for submission, I want `process_submission_callback` to be called. Can you please make a note of it?

> _Worker_: Sure _Queue_, I will invoke `process_submission_callback` whenever you receive a new message.



When a worker starts, it fetches active challenges from the database and then loads all the challenge evaluation scripts in a variable called `EVALUATION_SCRIPTS`, with challenge id as its key. The map would look like

```
EVALUATION_SCRIPTS = {
    <challenge_pk> : <evalutaion_script_loaded_as_module>,
    ....
}
```

After the challenges are successfully loaded, it creates a connection with the RabbitMQ Exchange `evalai_submissions` and then listens on the queue `submission_task_queue` with a binding key of `submission.*.*`.


### How is submission made?

When the user makes a submission on the frontend, the following actions happen sequentially

* As soon as the user submits a submission, a REST API with the URL pattern `jobs:challenge_submission` is called.

* This API fetches the challenge and its corresponding challenge phase.

* This API then checks if the challenge is active and challenge phase is public.

* It fetches the participant team's ID and its corresponding object.

* After all these checks are complete, a submission object is saved. The saved submission object includes __participant team id__ and __challenge phase id__ and __username__ of the participant creating it.

* At the end, a submission message is published to exchange `evalai_submissions` with a routing key of `submission.*.*`.

### Format of submission messages

The format of the message is

```
{
    "challenge_id": <challenge_pk_here>,
    "phase_id": <challenge_phase_pk_here>,
    "submission_id": <submission_pk_here>
}
```

This message is published with a routing key of `submission.*.*`


### How workers process submission message

Upon receiving a message from `submission_task_queue` with a binding key of `submission.*.*`, `process_submission_callback` is called. This function does the following:

* It fetches the challenge phase and submission object from the database using the challenge phase id and submission id received in the message.

* It then downloads the required files like input_file, etc. for submission in its computation directory.

* After this, the submission is run. Submission is initially marked in __RUNNING__ state. The `evaluate` function of `EVALUATION_SCRIPTS` map with key of the challenge id is called. The `evaluate` function takes in the annotation file path, the user annotation file path, and the challenge phase's code name as arguments. Running a submission involves temporarily updating `stderr` and `stdout` to different locations other than standard locations. This is done so as to capture the output and any errors produced when running the submission.

* The output from the `evaluate` function is stored in a variable called `submission_output`. Currently, the only way to check for the occurrence of an error is to check if the key `result` exists in `submission_output`.

    * If the key does not exist, then the submission is marked as __FAILED__.
    * If the key exists, then the variable `submission_output` is parsed and `DataSetSplit` objects are created. LeaderBoardData objects are also created (in bulk) with the required parameters. Finally, the submission is marked as __FINISHED__.

* The value in the temporarily updated `stderr` and `stdout` are stored in files named `stderr.txt` and `stdout.txt` which are then stored in the submission instance.

* Finally, the temporary computation directory allocated for this submission is removed.

### Notes

* REST API with url pattern `jobs:challenge_submission`. Here _jobs_ is application namespace and _challenge_submission_ is instance namespace. You can read more about [url namespace](https://docs.djangoproject.com/en/1.10/topics/http/urls/#url-namespaces)
