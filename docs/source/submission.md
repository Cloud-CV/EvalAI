## Submission

### How a submission is processed ?

We are using REST API's along with Queue based architecture to process submissions. When a participant makes a submission for a challenge, a REST API with url pattern `jobs:challenge_submission` is called. This API does the task of creating a new entry for submission model and then publishes a message to exchange `evalai_submissions` with a routing key of `submission.*.*`.

     User makes   --> API  --> Publish  --> RabbitMQ  --> Queue  --> Submission
    a submission               message      Exchange                  worker(s)


Exchange receives the message and then routes it to the queue `submission_task_queue`. At the end of `submission_task_queue` are workers(scripts/workers/submission_worker.py) which processes the submission message.

The worker can be run by

```
# assuming the current working directory is where manage.py lives
python scripts/workers/submission_worker.py
```

### How submission worker works ?

Submission worker is a python script which is mostly run as a daemon on production server and simply as a python process in development environment. To run submission worker in development environment,

```
python scripts/workers/submission_worker.py
```

Before a worker fully starts, it does the following actions

* Creates a new temporary directory for storing all its data files.

* Fetches the list of active challenges from the database. Active challenges are those published challenges whose start date is less than present time but end data is greater than present time. It loads all the evaluation scripts of challenges in a variable called `EVALUATION_SCRIPTS` with challenge id as its key, So the maps looks like

    ```
    EVALUATION_SCRIPTS = {
        <challenge_pk> : <evalutaion_script_loaded_as_module>,
        ....
    }
    ```

* Creates a connection with RabbitMQ by using the connection parameters specified in `settings.RABBITMQ_PARAMETERS`.

* After the connection is successfully created, a exchange with name `evalai_submissions` is created.
Also two queues one for processing submission message namely `submission_task_queue` and other for getting add challenge message is created.

* `submission_task_queue` is then binded with the routing key of `submission.*.*` and add challenge message queue is binded with a key of `challenge.add.*`
When ever a queue is binded to a exchange with any key, it means that as soon as the exchange receives a message with a key, it will route the message to the corresponding queue.

* Binding to any queue is also accompanied with a callback which basically takes as argument a function. This function specifies what should be done when the queue receives a message.

Eg: `submission_task_queue` is using `process_submission_callback` as a function which means that when ever any message is received in the queue, `process_submission_callback` will be called with the message as argument.

Expressing it informally it will be something like

> _Queue_: Hey _Exchange_, I am `submission_task_queue`. I will be listening to messages from you on binding key of `submission.*.*`

> _Exchange_: Hey _Queue_, Sure when ever I will receive any message with a routing key of `submission.*.*`, I will give it to you

> _Queue_: Thanks a lot.

> _Queue_: Hey _Worker_, Just for the record when ever I receive a new message for submission, I want `process_submission_callback` to be called. Can you please make a note of it ?

> _Worker_: Sure _Queue_, I will keep in mind to invoke `process_submission_callback` whenever you receive any new message



When a worker starts it fetches active challenges from the database and then loads all the evaluation scripts of challenges in a variable called `EVALUATION_SCRIPTS` with challenge id as its key, So the maps looks like

```
EVALUATION_SCRIPTS = {
    <challenge_pk> : <evalutaion_script_loaded_as_module>,
    ....
}
```

After the challenges are successfully loaded, it creates a connection with RabbitMQ Exchange `evalai_submissions` and then listens on the queue `submission_task_queue` with a binding key of `submission.*.*`.


### How submission is made ?

When the user makes submission on the frontend, following actions happen sequentially

* As soon as the user submits a submission, a REST API with url pattern `jobs:challenge_submission` is called.

* This API fetches the challenge and its corresponding challenge phase.

* This API then checks if the challenge is active and challenge phase is public

* It fetches id of participant team and its corresponding object.

* After all these checks are complete, a submission object is saved. The saved submission object includes __participant team id__ and __challenge phase id__ and __username__ of the participant creating it.

* At the end, a submission message is published to exchange `evalai_submissions` with a routing key of `submission.*.*`.

### Format of submission message

The format of the message is

```
{
    "challenge_id": <challenge_pk_here>,
    "phase_id": <challenge_phase_pk_here>,
    "submission_id": <submission_pk_here>
}
```

This message is published with a routing key of `submission.*.*`


### How worker processes submission message

On receiving a message from queue `submission_task_queue` with a binding key of `submission.*.*`, `process_submission_callback` is called. This function does the following:

* It fetches challenge phase and submission object from the database using challenge phase id and submission id received in the message.

* It then downloads the required necessary files like input_file, etc. for submission in its computation directory.

* After this, submission is run. Submission is initially marked in __RUNNING__ state. `evaluate` function of `EVALUATION_SCRIPTS` map with key of challenge id is called. The `evaluate` function receives annotation file path, user annotation file path and code name of challenge phase as argument. Also running a submission involves temporarily updating stderr and stdout to different locations other than standard locations. This is done so as to capture the output and error produced when running the submission.

* The output from `evaluate` function is stored in a variable called `submission_output`. Presently the only condition to check if a error has occurred or not is just to check if the key `result` exists in `submission_output`.

    * If the key does not exist, then submission is marked in status __FAILED__.
    * If the key exists, then the variable `submission_output` is parsed and accordingly `DataSetSplit` objects are created. Also LeaderBoardData object is created(in bulk) with the required parameters. Finally a submission is marked as __FINISHED__.

* At last the value in temporarily updated `stderr` and `stdout` are stored in files namely `stderr.txt` and `stdout.txt` which are further stored in submission instance.

* After all this is done, the temporary computation directory allocated just for this submission is removed.

### Notes

* 



api with url pattern `jobs:challenge_submission`. Here _jobs_ is application namespace and _challenge_submission_ is instance namespace. You can read more about [url namespace](https://docs.djangoproject.com/en/1.10/topics/http/urls/#url-namespaces)

