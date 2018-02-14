## Architectural Decisions

This is a collection of records for architecturally significant decisions.

### URL Patterns

We follow a very basic, yet strong convention for URLs, so that our rest APIs are properly namespaced. First of all, we rely heavily on HTTP verbs to perform **CRUD** actions.

For example, to perform **CRUD** operation on _Challenge Host Model_, the following URL patterns will be used.

* `GET /hosts/challenge_host_team` - Retrieves a list of challenge host teams

* `POST /hosts/challenge_host_team` - Creates a new challenge host team

* `GET /hosts/challenge_host_team/<challenge_host_team_id>` - Retrieves a specific challenge host team

* `PUT /hosts/challenge_host_team/<challenge_host_team_id>` - Updates a specific challenge host team

* `PATCH /hosts/challenge_host_team/<challenge_host_team_id>` - Partially updates a specific challenge host team

* `DELETE /hosts/challenge_host_team/<challenge_host_team_id>` - Deletes a specific challenge host team

Also, we have namespaced the URL patterns on a per-app basis, so URLs for _Challenge Host Model_, which is in the _hosts_ app, will be

```
/hosts/challenge_host_team
```

This way, one can easily identify where a particular API is located.

We use underscore **_** in URL patterns.

### Processing submission messages asynchronously

When a submission message is made, a REST API is called which saves the data related to the submission in the database. A submission involves the processing and evaluation of `input_file`. This file is used to evaluate the submission and then decide the status of the submission, whether it is _FINISHED_ or _FAILED_.

One way to process the submission is to evaluate it as soon as it is made, hence blocking the participant's request. Blocking the request here means to send the response to the participant only when the submission has been made and its output is known. This would work fine if the number of the submissions made is very low, but this is not the case.

Hence we decided to process and evaluate submission message in an asynchronous manner. To process the messages this way, we need to change our architecture a bit and add a Message Framework, along with a worker so that it can process the message.

Out of all the awesome messaging frameworks available, we have chosen RabbitMQ because of its transactional nature and reliability. Also, RabbitMQ is easily horizontally scalable, which means we can easily handle the heavy load by simply adding more nodes to the cluster.

For the worker, we went ahead with a normal python worker, which simply runs a process and loads all the required data in its memory. As soon as the worker starts, it listens on a RabbitMQ queue named `submission_task_queue` for new submission messages.

### Submission Worker

The submission worker are responsible for processing submission messages. It listens on a queue named `submission_task_queue`, and on receiving a message for a submission, it processes and evaluates the submission.

One of the major design changes that we decided to implement in the submission worker was to load all the data related to the challenge in the worker's memory, instead of fetching it every time a new submission message arrives. So the worker, when starting, fetches the list of active challenges from the database and then loads it into memory by maintaining the map `EVALUATION_SCRIPTS` on challenge id. This was actually a major performance improvement.

Another major design change that we incorporated here was to dynamically import the challenge module and to load it in the map instead of invoking a new python process every time a submission message arrives. So now whenever a new message for a submission is received, we already have its corresponding challenge module being loaded in a map called `EVALUATION_SCRIPTS`, and we just need to call

```
EVALUATION_SCRIPTS[challenge_id].evaluate(*params)
```

This was again a major performance improvement, which saved us from the task of invoking and managing Python processes to evaluate submission messages. Also, invoking a new python process every time for a new submission would have been really slow.
