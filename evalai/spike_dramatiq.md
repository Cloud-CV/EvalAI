# Check the feasibility of using dramatiq instead of Celery
* Motivation
   -
   - ElasticMQ was initially incorporated into the EvalAI project when we moved from RabbitMQ to AWS SQS in the production environment. This was done so as to enable a SQS-style interface in developer mode to mock the same.
   - Refer: https://github.com/Cloud-CV/EvalAI/pull/1752
   - But as per recent builds, while Celery works with SQS, it seems incompatible with ElasticMQ.
   - Refer: https://github.com/celery/celery/issues/5406
   - Therefore we are having to move to another broker which supports ElasticMQ and this report looks into [dramatiq](https://github.com/bogdanp/dramatiq_sqs) as an option for the same.
* Required changes:
  -
  - Dependency changes
  - API changes
  - Settings changes per environment
 * Dependency Changes:
   -
   Thankfully, dramatiq doesn't ask for much more. The only extra packages required currently along with the versions are:
    - django-dramatiq==0.8.0  (if compatible)
    - dramatiq==1.7.0
    - dramatiq-sqs==0.0.10
    - prometheus-client==0.7.1
 * <b>An overview of the dependencies:</b>
   - django-dramatiq is a pluggable django app for integration with Dramatiq. GitHub link: https://github.com/bogdanp/django_dramatiq
   - dramatiq is the task queue management tool we want to use, the documentation is concise and easy-to-grasp: https://dramatiq.io
   - dramatiq-sqs provides us the broker to be used with SQS. In our case, we will be using it with ElasticMQ.
 * API changes
   -
   * The API for dramatiq is easy-to-understand.
   * A python function can be converted into an *actor* (app.task in celery) by adding a dramatiq.actor decorator. See [actors](https://dramatiq.io/guide.html#actors).
   * When this actor function is called with a syntax as `function.send(args)`, a message is sent to the intended queue. This is similar to `function.delay(args)` in Celery.
   * Like the workers in celery have to be activate with `celery -A tasks worker --loglevel=info`, it has to be run in dramatiq as `python manage.py rundramatiq`.
   * To get a clearer idea of codebase differences in EvalAI, please refer: https://github.com/Cloud-CV/EvalAI/pull/2583/files
 * Settings changes per  environment
   -
   - Celery works well with AWS SQS in production. It is also well-documented and can be continued in the future.
   - Dramatiq is not as well documented and we may face trouble updating in the future.
   - At least for now, we should implement dramatiq only in development settings. The changes will thus have to be specific to the dev environments.
   - Please see: https://github.com/Cloud-CV/EvalAI/pull/2583/files
* Time and work estimate:
  -
  - It should be relatively easy to make the mentioned changes.
  - However, because dramatiq (especially django_dramatiq or dramatiq_sqs) have not seen much exposure, testing and debugging should be given enough time.
  - Human-as-user testing should be done to ensure that the newly added components are working as expected.
  - As mentioned, the API changes will be relatively easy, and should take less than a week.
  - As opposed to this, the testing and debugging should go on for at least a few more weeks under different conditions so that we can document the necessary environment settings.
  - For example, `dramatiq_sqs.SQSBroker` is not compatible with Python3.5 (which comes by default in Ubuntu 16.04).  See: https://github.com/Bogdanp/dramatiq_sqs/issues/3
* Pros:
  -
  - The [`django_dramatiq`](https://github.com/bogdanp/django_dramatiq)  library is great for our and comes in the form of a pluggable app.
  -  The broker ([dramatiq_sqs](https://github.com/bogdanp/dramatiq_sqs)) is really easy to configure and this gives an edge over celery.
  - Easy-to-understand API, can be migrated easily
* Cons:
  -
  - Poorly documented
  - The SQSBroker (dramatiq_sqs) does not have many users. It has a lack of  tutorials and contributors. The latest update to dramatiq_sqs was made in 2018
  - Not as customizable as Celery (but satisfies our use case very well).
  - Needs some prior testing before being implemented in development/production environments.
