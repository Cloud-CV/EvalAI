# Apps : 77.89%
<details>
    <summary>View Files</summary> 
    <br>
## base

### Utils.py 

<details>
    <summary>View Code</summary> 
    <br>
     <br> Email sending </br> 
```
def encode_data(data):
    """
    Turn `data` into a hash and an encoded string, suitable for use with `decode_data`.
    """
    encoded = []
    for i in data:
        encoded.append(base64.encodestring(i).split("=")[0])
    return encoded
def decode_data(data):
    """
    The inverse of `encode_data`.
    """
    decoded = []
    for i in data:
        decoded.append(base64.decodestring(i + "=="))
    return decoded
def send_email(
    sender=settings.CLOUDCV_TEAM_EMAIL,
    recepient=None,
    template_id=None,
    template_data={},
):
    """Function to send email
    Keyword Arguments:
        sender {string} -- Email of sender (default: {settings.TEAM_EMAIL})
        recepient {string} -- Recepient email address
        template_id {string} -- Sendgrid template id
        template_data {dict} -- Dictionary to substitute values in subject and email body
    """
    try:
        sg = sendgrid.SendGridAPIClient(
            apikey=os.environ.get("SENDGRID_API_KEY")
        )
        sender = Email(sender)
        mail = Mail()
        mail.from_email = sender
        mail.template_id = template_id
        to_list = Personalization()
        to_list.dynamic_template_data = template_data
        to_email = Email(recepient)
        to_list.add_to(to_email)
        mail.add_personalization(to_list)
        sg.client.mail.send.post(request_body=mail.get())
    except Exception:
        logger.warning(
            "Cannot make sendgrid call. Please check if SENDGRID_API_KEY is present."
        )
    return
def get_url_from_hostname(hostname):
    if settings.DEBUG or settings.TEST:
        scheme = "http"
    else:
        scheme = "https"
    url = "{}://{}".format(scheme, hostname)
    return url
```
 <br> Submission queue for Evalai </br> 

```
return client
    except Exception as e:
        logger.exception(e)
def get_sqs_queue_object():
    if settings.DEBUG or settings.TEST:
        queue_name = "evalai_submission_queue"
        sqs = boto3.resource(
            "sqs",
            endpoint_url=os.environ.get("AWS_SQS_ENDPOINT", "http://sqs:9324"),
            region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY", "x"),
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID", "x"),
        )
    else:
        sqs = boto3.resource(
            "sqs",
            region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        )
    # Check if the queue exists. If no, then create one
    try:
        queue = sqs.get_queue_by_name(QueueName=queue_name)
    except botocore.exceptions.ClientError as ex:
        if (
            ex.response["Error"]["Code"]
            != "AWS.SimpleQueueService.NonExistentQueue"
        ):
            logger.exception("Cannot get queue: {}".format(queue_name))
        queue = sqs.create_queue(QueueName=queue_name)
    return queue
```
 <br> Exception while sending slack notification </br> 

```
return requests.post(
            webhook,
            data=json.dumps(data),
            headers={"Content-Type": "application/json"}
        )
    except Exception as e:
        logger.exception(
            "Exception raised while sending slack notification. \n Exception message: {}".format(e)
        )
def mock_if_non_prod_aws(aws_mocker):
    def decorator(func):
        if not (settings.DEBUG or settings.TEST):
            return func
        return aws_mocker(func)
    return decorator
```

</br>
</details>

### management/commands/seed.py

<details>
    <summary>View Code</summary>
    <br>
  <br> database seeder </br>    
```
class Command(BaseCommand):
    help = "Seeds the database with random but sensible values."
    def add_arguments(self, parser):
        parser.add_argument(
            "-nc", nargs="?", default=1, type=int, help="Number of challenges."
        )
    def handle(self, *args, **options):
        self.nc = options["nc"]
        self.stdout.write(
            self.style.SUCCESS("Starting the database seeder. Hang on...")
        )
        call_command("runscript", "seed", "--script-args", self.nc)
```

</br>
</details>

### apps.py

<details>
    <summary>View Code</summary>
    <br>
    
```
class BaseConfig(AppConfig):
    name = "base"
```

</br>
</details>

## challenges

### admin

<details>
    <summary>View Code</summary>
    <br>
     <br> Errors in various functions of select workers</br> 
```
 def start_selected_workers(self, request, queryset):
        response = start_workers(queryset)
        count, failures = response["count"], response["failures"]
        if count == queryset.count():
            message = "All selected challenge workers successfully started."
            messages.success(request, message)
        else:
            messages.success(
                request,
                "{} challenge workers were succesfully started.".format(count),
            )
            for fail in failures:
                challenge_pk, message = fail["challenge_pk"], fail["message"]
                display_message = "Challenge {}: {}".format(
                    challenge_pk, message
                )
                messages.error(request, display_message)
    start_selected_workers.short_description = (
        "Start all selected challenge workers."
    )
    def stop_selected_workers(self, request, queryset):
        response = stop_workers(queryset)
        count, failures = response["count"], response["failures"]
        if count == queryset.count():
            message = "All selected challenge workers successfully stopped."
            messages.success(request, message)
        else:
            messages.success(
                request,
                "{} challenge workers were succesfully stopped.".format(count),
            )
            for fail in failures:
                challenge_pk, message = fail["challenge_pk"], fail["message"]
                display_message = "Challenge {}: {}".format(
                    challenge_pk, message
                )
                messages.error(request, display_message)
    stop_selected_workers.short_description = (
        "Stop all selected challenge workers."
    )
    def scale_selected_workers(self, request, queryset):
        num_of_tasks = int(request.POST["num_of_tasks"])
        if num_of_tasks >= 0 and num_of_tasks % 1 == 0:
            response = scale_workers(queryset, num_of_tasks)
            count, failures = response["count"], response["failures"]
            if count == queryset.count():
                message = "All selected challenge workers successfully scaled."
                messages.success(request, message)
            else:
                messages.success(
                    request,
                    "{} challenge workers were succesfully scaled.".format(
                        count
                    ),
                )
                for fail in failures:
                    challenge_pk, message = (
                        fail["challenge_pk"],
                        fail["message"],
                    )
                    display_message = "Challenge {}: {}".format(
                        challenge_pk, message
                    )
                    messages.error(request, display_message)
        else:
            messages.warning(
                request, "Please enter a valid whole number to scale."
            )
    scale_selected_workers.short_description = (
        "Scale all selected challenge workers to a given number."
    )
    def restart_selected_workers(self, request, queryset):
        response = restart_workers(queryset)
        count, failures = response["count"], response["failures"]
        if count == queryset.count():
            message = "All selected challenge workers successfully restarted."
            messages.success(request, message)
        else:
            messages.success(
                request,
                "{} challenge workers were succesfully restarted.".format(
                    count
                ),
            )
            for fail in failures:
                challenge_pk, message = fail["challenge_pk"], fail["message"]
                display_message = "Challenge {}: {}".format(
                    challenge_pk, message
                )
                messages.error(request, display_message)
    restart_selected_workers.short_description = (
        "Restart all selected challenge workers."
    )
    def delete_selected_workers(self, request, queryset):
        response = delete_workers(queryset)
        count, failures = response["count"], response["failures"]
        if count == queryset.count():
            message = "All selected challenge workers successfully deleted."
            messages.success(request, message)
        else:
            messages.success(
                request,
                "{} challenge workers were succesfully deleted.".format(count),
            )
            for fail in failures:
                challenge_pk, message = fail["challenge_pk"], fail["message"]
                display_message = "Challenge {}: {}".format(
                    challenge_pk, message
                )
                messages.error(request, display_message)
```

</br>
</details>

### apps.py

<details>
    <summary>View Code</summary>
    <br>
    
```
class ChallengesConfig(AppConfig):
    name = "challenges"
```

</br>
</details>

### aws_utils.py

<details>
    <summary>View Code</summary>
    <br>
 <br> It is not tested at all </br> 
```
def client_token_generator():
    """
    Returns a 32 characters long client token to ensure idempotency with create_service boto3 requests.
    Parameters: None
    Returns:
    str: string of size 32 composed of digits and letters
    """
    client_token = "".join(
        random.choices(string.ascii_letters + string.digits, k=32)
    )
    return client_token
def register_task_def_by_challenge_pk(client, queue_name, challenge):
    """
    Registers the task definition of the worker for a challenge, before creating a service.
    Parameters:
    client (boto3.client): the client used for making requests to ECS.
    queue_name (str): queue_name is the queue field of the Challenge model used in many parameters fof the task def.
    challenge (<class 'challenges.models.Challenge'>): The challenge object for whom the task definition is being registered.
    Returns:
    dict: A dict of the task definition and it's ARN if succesful, and an error dictionary if not
    """
    container_name = "worker_{}".format(queue_name)
    execution_role_arn = COMMON_SETTINGS_DICT["EXECUTION_ROLE_ARN"]
    if execution_role_arn:
        definition = task_definition.format(
            queue_name=queue_name,
            container_name=container_name,
            ENV=ENV,
            challenge_pk=challenge.pk,
            **COMMON_SETTINGS_DICT
        )
        definition = eval(definition)
        if not challenge.task_def_arn:
            try:
                response = client.register_task_definition(**definition)
                if (
                    response["ResponseMetadata"]["HTTPStatusCode"]
                    == HTTPStatus.OK
                ):
                    task_def_arn = response["taskDefinition"][
                        "taskDefinitionArn"
                    ]
                    challenge.task_def_arn = task_def_arn
                    challenge.save()
                return response
            except ClientError as e:
                logger.exception(e)
                return e.response
        else:
            message = "Error. Task definition already registered for challenge {}.".format(
                challenge.pk
            )
            return {
                "Error": message,
                "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
            }
    else:
        message = "Please ensure that the TASK_EXECUTION_ROLE_ARN is appropriately passed as an environment varible."
        return {
            "Error": message,
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
        }
def create_service_by_challenge_pk(client, challenge, client_token):
    """
    Creates the worker service for a challenge, and sets the number of workers to one.
    Parameters:
    client (boto3.client): the client used for making requests to ECS
    challenge (<class 'challenges.models.Challenge'>): The challenge object  for whom the task definition is being registered.
    client_token (str): The client token generated by client_token_generator()
    Returns:
    dict: The response returned by the create_service method from boto3. If unsuccesful, returns an error dictionary
    """
    queue_name = challenge.queue
    service_name = "{}_service".format(queue_name)
    if (
        challenge.workers is None
    ):  # Verify if the challenge is new (i.e, service not yet created.).
        if challenge.task_def_arn == "" or challenge.task_def_arn is None:
            response = register_task_def_by_challenge_pk(
                client, queue_name, challenge
            )
            if response["ResponseMetadata"]["HTTPStatusCode"] != HTTPStatus.OK:
                return response
        task_def_arn = challenge.task_def_arn
        definition = service_definition.format(
            CLUSTER=COMMON_SETTINGS_DICT["CLUSTER"],
            service_name=service_name,
            task_def_arn=task_def_arn,
            client_token=client_token,
            **VPC_DICT
        )
        definition = eval(definition)
        try:
            response = client.create_service(**definition)
            if response["ResponseMetadata"]["HTTPStatusCode"] == HTTPStatus.OK:
                challenge.workers = 1
                challenge.save()
            return response
        except ClientError as e:
            logger.exception(e)
            return e.response
    else:
        message = "Worker service for challenge {} already exists. Please scale, stop or delete.".format(
            challenge.pk
        )
        return {
            "Error": message,
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
        }
def update_service_by_challenge_pk(
    client, challenge, num_of_tasks, force_new_deployment=False
):
    """
    Updates the worker service for a challenge, and scales the number of workers to num_of_tasks.
    Parameters:
    client (boto3.client): the client used for making requests to ECS
    challenge (<class 'challenges.models.Challenge'>): The challenge object  for whom the task definition is being registered.
    num_of_tasks (int): Number of workers to scale to for the challenge.
    force_new_deployment (bool): Set True (mainly for restarting) to specify if you want to redploy with the latest image from ECR. Default is False.
    Returns:
    dict: The response returned by the update_service method from boto3. If unsuccesful, returns an error dictionary
    """
    queue_name = challenge.queue
    service_name = "{}_service".format(queue_name)
    task_def_arn = challenge.task_def_arn
    kwargs = update_service_args.format(
        CLUSTER=COMMON_SETTINGS_DICT["CLUSTER"],
        service_name=service_name,
        task_def_arn=task_def_arn,
        force_new_deployment=force_new_deployment,
    )
    kwargs = eval(kwargs)
    try:
        response = client.update_service(**kwargs)
        if response["ResponseMetadata"]["HTTPStatusCode"] == HTTPStatus.OK:
            challenge.workers = num_of_tasks
            challenge.save()
        return response
    except ClientError as e:
        logger.exception(e)
        return e.response
def delete_service_by_challenge_pk(challenge):
    """
    Deletes the workers service of a challenge.
    Before deleting, it scales down the number of workers in the service to 0, then proceeds to delete the service.
    Parameters:
    challenge (<class 'challenges.models.Challenge'>): The challenge object for whom the task definition is being registered.
    Returns:
    dict: The response returned by the delete_service method from boto3
    """
    client = get_boto3_client("ecs", aws_keys)
    queue_name = challenge.queue
    service_name = "{}_service".format(queue_name)
    kwargs = delete_service_args.format(
        CLUSTER=COMMON_SETTINGS_DICT["CLUSTER"],
        service_name=service_name,
        force=True,
    )
    kwargs = eval(kwargs)
    try:
        if challenge.workers != 0:
            response = update_service_by_challenge_pk(
                client, challenge, 0, False
            )
            if response["ResponseMetadata"]["HTTPStatusCode"] != HTTPStatus.OK:
                return response
        response = client.delete_service(**kwargs)
        if response["ResponseMetadata"]["HTTPStatusCode"] == HTTPStatus.OK:
            challenge.workers = None
            challenge.save()
            client.deregister_task_definition(
                taskDefinition=challenge.task_def_arn
            )
            challenge.task_def_arn = ""
            challenge.save()
        return response
    except ClientError as e:
        logger.exception(e)
        return e.response
def service_manager(
    client, challenge, num_of_tasks=None, force_new_deployment=False
):
    """
    This method determines if the challenge is new or not, and accordingly calls <update or create>_by_challenge_pk.
    Called by: Start, Stop & Scale methods for multiple workers.
    Parameters:
    client (boto3.client): the client used for making requests to ECS.
    challenge (): The challenge object for whom the task definition is being registered.
    num_of_tasks: The number of workers to scale to (relevant only if the challenge is not new).
                  default: None
    Returns:
    dict: The response returned by the respective functions update_service_by_challenge_pk or create_service_by_challenge_pk
    """
    if challenge.workers is not None:
        response = update_service_by_challenge_pk(
            client, challenge, num_of_tasks, force_new_deployment
        )
        return response
    else:
        client_token = client_token_generator()
        response = create_service_by_challenge_pk(
            client, challenge, client_token
        )
        return response
def start_workers(queryset):
    """
    The function called by the admin action method to start all the selected workers.
    Calls the service_manager method. Before calling, checks if all the workers are incactive.
    Parameters:
    queryset (<class 'django.db.models.query.QuerySet'>): The queryset of selected challenges in the django admin page.
    Returns:
    dict: keys-> 'count': the number of workers successfully started.
                 'failures': a dict of all the failures with their error messages and the challenge pk
    """
    client = get_boto3_client("ecs", aws_keys)
    count = 0
    failures = []
    for challenge in queryset:
        if (challenge.workers == 0) or (challenge.workers is None):
            response = service_manager(
                client, challenge=challenge, num_of_tasks=1
            )
            if response["ResponseMetadata"]["HTTPStatusCode"] != HTTPStatus.OK:
                failures.append(
                    {
                        "message": response["Error"],
                        "challenge_pk": challenge.pk,
                    }
                )
                continue
            count += 1
        else:
            response = "Please select challenge with inactive workers only."
            failures.append(
                {"message": response, "challenge_pk": challenge.pk}
            )
    return {"count": count, "failures": failures}
def stop_workers(queryset):
    """
    The function called by the admin action method to stop all the selected workers.
    Calls the service_manager method. Before calling, verifies that the challenge is not new, and is active.
    Parameters:
    queryset (<class 'django.db.models.query.QuerySet'>): The queryset of selected challenges in the django admin page.
    Returns:
    dict: keys-> 'count': the number of workers successfully stopped.
                 'failures': a dict of all the failures with their error messages and the challenge pk
    """
    client = get_boto3_client("ecs", aws_keys)
    count = 0
    failures = []
    for challenge in queryset:
        if (challenge.workers is not None) and (challenge.workers > 0):
            response = service_manager(
                client, challenge=challenge, num_of_tasks=0
            )
            if response["ResponseMetadata"]["HTTPStatusCode"] != HTTPStatus.OK:
                failures.append(
                    {
                        "message": response["Error"],
                        "challenge_pk": challenge.pk,
                    }
                )
                continue
            count += 1
        else:
            response = "Please select challenges with active workers only."
            failures.append(
                {"message": response, "challenge_pk": challenge.pk}
            )
    return {"count": count, "failures": failures}
def scale_workers(queryset, num_of_tasks):
    """
    The function called by the admin action method to scale all the selected workers.
    Calls the service_manager method. Before calling, checks if the target scaling number is different than current.
    Parameters:
    queryset (<class 'django.db.models.query.QuerySet'>): The queryset of selected challenges in the django admin page.
    Returns:
    dict: keys-> 'count': the number of workers successfully started.
                 'failures': a dict of all the failures with their error messages and the challenge pk
    """
    client = get_boto3_client("ecs", aws_keys)
    count = 0
    failures = []
    for challenge in queryset:
        if challenge.workers is None:
            response = "Please start worker(s) before scaling."
            failures.append(
                {"message": response, "challenge_pk": challenge.pk}
            )
            continue
        if num_of_tasks == challenge.workers:
            response = "Please scale to a different number. Challenge has {} worker(s).".format(
                num_of_tasks
            )
            failures.append(
                {"message": response, "challenge_pk": challenge.pk}
            )
            continue
        response = service_manager(
            client, challenge=challenge, num_of_tasks=num_of_tasks
        )
        if response["ResponseMetadata"]["HTTPStatusCode"] != HTTPStatus.OK:
            failures.append(
                {"message": response["Error"], "challenge_pk": challenge.pk}
            )
            continue
        count += 1
    return {"count": count, "failures": failures}
def delete_workers(queryset):
    """
    The function called by the admin action method to delete all the selected workers.
    Calls the delete_service_by_challenge_pk method. Before calling, verifies that the challenge is not new.
    Parameters:
    queryset (<class 'django.db.models.query.QuerySet'>): The queryset of selected challenges in the django admin page.
    Returns:
    dict: keys-> 'count': the number of workers successfully stopped.
                 'failures': a dict of all the failures with their error messages and the challenge pk
    """
    count = 0
    failures = []
    for challenge in queryset:
        if challenge.workers is not None:
            response = delete_service_by_challenge_pk(challenge=challenge)
            if response["ResponseMetadata"]["HTTPStatusCode"] != HTTPStatus.OK:
                failures.append(
                    {
                        "message": response["Error"],
                        "challenge_pk": challenge.pk,
                    }
                )
                continue
            count += 1
        else:
            response = "Please select challenges with active workers only."
            failures.append(
                {"message": response, "challenge_pk": challenge.pk}
            )
    return {"count": count, "failures": failures}
```

</br>
</details>
</br>
</details>
## jobs
<details>
    <summary>View Files</summary>
    <br>
### sender.py

<details>
    <summary>View Code</summary>
    <br>
 <br> Challenge ID prompt error message </br>     
```
except Challenge.DoesNotExist:
        logger.exception(
            "Challenge does not exist for the given id {}".format(challenge_pk)
        )
        return
```

</br>
</details>

### tasks.py

<details>
    <summary>View Code</summary>
    <br>
 <br> Submission from url </br> 
```
@app.task
def download_file_and_publish_submission_message(
    request_data,
    user_pk,
    request_method,
    challenge_phase_id
):
    """
    Download submission file from url and send it for the evaluation
    """
    user = User.objects.get(pk=user_pk)
    challenge_phase = ChallengePhase.objects.get(
        pk=challenge_phase_id
    )
    participant_team_id = get_participant_team_id_of_user_for_a_challenge(
        user, challenge_phase.challenge.pk
    )
    participant_team = ParticipantTeam.objects.get(
        pk=participant_team_id
    )
    request = HttpRequest()
    request.method = request_method
    request.user = user
    try:
        downloaded_file = get_file_from_url(request_data["file_url"])
        file_path = os.path.join(downloaded_file["temp_dir_path"], downloaded_file["name"])
        with open(file_path, 'rb') as f:
            input_file = SimpleUploadedFile(
                downloaded_file["name"],
                f.read(),
                content_type="multipart/form-data"
            )
        data = {
            "input_file": input_file,
            "method_name": request_data["method_name"],
            "method_description": request_data["method_description"],
            "project_url": request_data["project_url"],
            "publication_url": request_data["publication_url"],
            "status": Submission.SUBMITTED
        }
        serializer = SubmissionSerializer(
            data=data,
            context={
                'participant_team': participant_team,
                'challenge_phase': challenge_phase,
                'request': request
            }
        )
        if serializer.is_valid():
            serializer.save()
            submission = serializer.instance
            # publish messages in the submission worker queue
            publish_submission_message(challenge_phase.challenge.pk, challenge_phase.pk, submission.pk)
            logger.info("Message published to submission worker successfully!")
            shutil.rmtree(downloaded_file['temp_dir_path'])
    except Exception as e:
        logger.exception(
            "Exception while downloading and sending submission for evaluation {}"
            .format(e)
        )
```

</br>
</details>

### utils.py

<details>
    <summary>View Code</summary>
    <br>
    <br> Check for submission limit</br>  
```
 if submissions_done_count >= max_submissions_count:
        response_data = {
            "message": "You have exhausted maximum submission limit!",
            "submission_limit_exceeded": True,
        }
        return response_data, status.HTTP_200_OK
    # Check for monthy submission limit
    elif submissions_done_this_month_count >= max_submissions_per_month_count:
        date_time_now = timezone.now()
        next_month_start_date_time = date_time_now + datetime.timedelta(
            days=+30
        )
        next_month_start_date_time = next_month_start_date_time.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        remaining_time = next_month_start_date_time - date_time_now
        if submissions_done_today_count >= max_submissions_per_day_count:
            response_data = {
                "message": "Both daily and monthly submission limits are exhausted!",
                "remaining_time": remaining_time,
            }
        else:
            response_data = {
                "message": "You have exhausted this month's submission limit!",
                "remaining_time": remaining_time,
            }
        return response_data, status.HTTP_200_OK
```
<br>Checks that a given URL is reachable</br>

```
def is_url_valid(url):
    """
    Checks that a given URL is reachable.
    :param url: A URL
    :return type: bool
    """
    request = urllib.request.Request(url)
    request.get_method = lambda: 'HEAD'
    try:
        urllib.request.urlopen(request)
        return True
    except urllib.request.HTTPError:
        return False
def get_file_from_url(url):
    """ Get file object from a url """
    BASE_TEMP_DIR = tempfile.mkdtemp()
    file_name = url.split("/")[-1]
    file_path = os.path.join(BASE_TEMP_DIR, file_name)
    file_obj = {}
    headers = {'user-agent': 'Wget/1.16 (linux-gnu)'}
    response = requests.get(url, stream=True, headers=headers)
    with open(file_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
    file_obj['name'] = file_name
    file_obj['temp_dir_path'] = BASE_TEMP_DIR
    return file_obj
```

</br>
</details>
</br>
</details>

# evalai : 72.22%
<details>
    <summary>View Files</summary>
    <br>
### celery.py
Full testing required
### urls.py

<details>
    <summary>View Code</summary>
    <br>
    
```
if settings.DEBUG:
    urlpatterns += [
        url(r"^dbschema/", include("django_spaghetti.urls")),
        url(r"^docs/", include("rest_framework_docs.urls")),
        url(
            r"^api/admin-auth/",
            include("rest_framework.urls", namespace="rest_framework"),
        ),
        url(r"^silk/", include("silk.urls", namespace="silk")),
    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

```

</br>
</details>
</br>
</details>

# frontend/src/js/controllers : 78.77%

<details>
    <summary>View Files</summary>
    <br>

### analyticsCtrl.js

<details>
    <summary>View Code</summary>
    <br>
<br> On success response for submission </br>
```
onSuccess: function(response) {
                                        var status = response.status;
                                        var details = response.data;
                                        if (status == 200) {
                                            for(var i=0; i<challengePhaseId.length; i++) {
                                                if (challengePhaseId[i] == details.challenge_phase) {
                                                    vm.totalSubmission[challengePhaseId[i]] = details.total_submissions;
                                                    vm.totalParticipatedTeams[challengePhaseId[i]] = details.participant_team_count;
                                                    i++;
                                                    break;
                                                }
                                            }
                                        }
                                    },

onSuccess: function(response) {
                                        var status = response.status;
                                        var details = response.data;
                                        if (status == 200) {
                                            for(var i=0; i<challengePhaseId.length; i++) {
                                                if (challengePhaseId[i] == response.data.challenge_phase) {
                                                    vm.lastSubmissionTime[challengePhaseId[i]] = details.last_submission_timestamp_in_challenge_phase;
                                                    i++;
                                                    break;
                                                }
                                            }
                                        }
                                    },
```
<br>Getting participants of a specific challenge ID</br>

```
  vm.downloadChallengeParticipantTeams = function() {
            parameters.url = "analytics/challenges/" + vm.challengeId + "/download_all_participants/";
                parameters.method = "GET";
                parameters.callback = {
                    onSuccess: function(response) {
                        var details = response.data;
                        var anchor = angular.element('<a/>');
                        anchor.attr({
                            href: 'data:attachment/csv;charset=utf-8,' + encodeURI(details),
                            download: 'participant_teams_' + vm.challengeId + '.csv'
                        })[0].click();
                    },
                    onError: function(response) {
                        var details = response.data;
                        $rootScope.notify('error', details.error);
                    }
                };
                utilities.sendRequest(parameters);
        };
```

</br>
</details>

### authCtrl.js

<details>
    <summary>View Code</summary>
    <br>
  <br>Check for various entries in sign up form</br>  
```
 if (response.status == 201) {
                            vm.isFormError = false;
                            // vm.regMsg = "Registered successfully, Login to continue!";
                            $rootScope.notify("success", "Registered successfully. Please verify your email address!");
                            $state.go('auth.login');
                        }
                        vm.stopLoader();
                    },
                    onError: function(response) {
                        if (response.status == 400) {
                            vm.stopLoader();
                            vm.isFormError = true;
                            var non_field_errors, isUsername_valid, isEmail_valid, isPassword1_valid, isPassword2_valid;
                            try {
                                non_field_errors = typeof(response.data.non_field_errors) !== 'undefined' ? true : false;
                                isUsername_valid = typeof(response.data.username) !== 'undefined' ? true : false;
                                isEmail_valid = typeof(response.data.email) !== 'undefined' ? true : false;
                                isPassword1_valid = typeof(response.data.password1) !== 'undefined' ? true : false;
                                isPassword2_valid = typeof(response.data.password2) !== 'undefined' ? true : false;
                                if (non_field_errors) {
                                    vm.FormError = response.data.non_field_errors[0];
                                } else if (isUsername_valid) {
                                    vm.FormError = response.data.username[0];
                                } else if (isEmail_valid) {
                                    vm.FormError = response.data.email[0];
                                } else if (isPassword1_valid) {
                                    vm.FormError = response.data.password1[0];
                                } else if (isPassword2_valid) {
                                    vm.FormError = response.data.password2[0];
                                }
                            } catch (error) {
                                $rootScope.notify("error", error);
                            }
                        }
                        vm.stopLoader();
                    }
```
<br>Password stregth check and alerts for error in signup form </br>

```
parameters.callback = {
                    onSuccess: function(response) {
                        if (response.status == 200) {
                            utilities.storeData('userKey', response.data.token);
                            if ($rootScope.previousState) {
                                $state.go($rootScope.previousState);
                                vm.stopLoader();
                            } else {
                                $state.go('web.dashboard');
                            }
                        } else {
                            alert("Something went wrong");
                        }
                    },
                    onError: function(response) {
                        if (response.status == 400) {
                            vm.isFormError = true;
                            var non_field_errors;
                            try {
                                non_field_errors = typeof(response.data.non_field_errors) !== 'undefined' ? true : false;
                                if (non_field_errors) {
                                    vm.FormError = response.data.non_field_errors[0];
                                }
                            } catch (error) {
                                $rootScope.notify("error", error);
                            }
                        }
                        vm.stopLoader();
                    }
                };
                utilities.sendRequest(parameters, "no-header");
            } else {
                vm.stopLoader();
            }
        };
        // function to check password strength
        vm.checkStrength = function(password) {
            var passwordStrength = utilities.passwordStrength(password);
            vm.message = passwordStrength[0];
            vm.color = passwordStrength[1];
        };

```
<br>Reset password function</br>

```
 password1_valid = typeof(response.data.new_password1) !== 'undefined' ? true : false;
                            password2_valid = typeof(response.data.new_password2) !== 'undefined' ? true : false;
                            if (token_valid) {
                                vm.FormError = "this link has been already used or expired.";
                            } else if (password1_valid) {
                                vm.FormError = Object.values(response.data.new_password1).join(" ");
                            } else if (password2_valid) {
                                vm.FormError = Object.values(response.data.new_password2).join(" ");
                            }
```

</br>
</details>

### challengeCtrl.js


<details>
    <summary>View Code</summary>
    <br>
<br>Not tested at all</br>

```
 var elementId = $location.absUrl().split('?')[0].split('#')[1];
                if (elementId) {
                    $anchorScroll.yOffset = 90;
                    $anchorScroll(elementId);
                    $scope.isHighlight = elementId.split("leaderboardrank-")[1];
                }
               
```

```
var newHash = elementId.toString();
            if ($location.hash() !== newHash) {
                $location.hash(elementId);
            } else {
                $anchorScroll();
            }
            $scope.isHighlight = false;
            $anchorScroll.yOffset = 90;
        };
```

```
 var details = response.data;
                                                        vm.existTeam = details;
                                                        // condition for pagination
                                                        if (vm.existTeam.next === null) {
                                                            vm.isNext = 'disabled';
                                                            vm.currentPage = vm.existTeam.count / 10;
                                                        } else {
                                                            vm.isNext = '';
                                                            vm.currentPage = parseInt(vm.existTeam.next.split('page=')[1] - 1);
                                                        }
                                                        if (vm.existTeam.previous === null) {
                                                            vm.isPrev = 'disabled';
                                                        } else {
                                                            vm.isPrev = '';
                                                        }
                                                        vm.stopLoader();
                                                    });
```

```
var error = response.data;
                                        utilities.storeData('emailError', error.detail);
                                        $state.go('web.permission-denied');
                                        utilities.hideLoader();
                                    }
```

```
 var participationState;
            if (isRegistrationOpen) {
                participationState = 'Close';
            } else {
                participationState = 'Open';
            }
            var confirm = $mdDialog.confirm()
                          .title(participationState + ' participation in the challenge?')
                          .ariaLabel('')
                          .targetEvent(ev)
                          .ok('Yes, I\'m sure')
                          .cancel('No');
            $mdDialog.show(confirm).then(function () {
                var challengeHostList = utilities.getData("challengeCreator");
                for (var challenge in challengeHostList) {
                    if (challenge == vm.challengeId) {
                        vm.challengeHostId = challengeHostList[challenge];
                        break;
                    }
                }
                parameters.method = "PATCH";
                parameters.url = "challenges/challenge_host_team/" + vm.challengeHostId + "/challenge/" + vm.challengeId;
                parameters.data = {
                    "is_registration_open": !isRegistrationOpen
                };
                parameters.callback = {
                    onSuccess: function() {
                        vm.isRegistrationOpen = !vm.isRegistrationOpen;
                        $rootScope.notify('success', 'Participation is ' + participationState + 'ed successfully');
                    },
                    onError: function(response) {
                        var details = response.data;
                        $rootScope.notify('error', details.error);
                    }
                };
                utilities.sendRequest(parameters);
            }, function() {});
        };

```

```
 var urlRegex = /(ftp|http|https):\/\/(\w+:{0,1}\w*@)?(\S+)(:[0-9]+)?(\/|\/([\w#!:.?+=&%@!\-/]))?/;
                        var validExtensions = ["json", "zip", "csv"];
                        var isUrlValid = urlRegex.test(vm.fileUrl);
                        var extension = vm.fileUrl.split(".").pop();
                        if (isUrlValid && validExtensions.includes(extension)) {
                            formData.append("file_url", vm.fileUrl);
                        } else {
                            vm.stopLoader();
                            vm.subErrors.msg = "Please enter a valid URL which ends in json, zip or csv file extension!";
                            return false;
```

```
 parameters.url = "jobs/" + "challenge_phase_split/" + vm.phaseSplitId + "/leaderboard/?page_size=1000";
                parameters.method = 'GET';
                parameters.data = {};
                parameters.callback = {
                    onSuccess: function(response) {
                        var details = response.data;
                        if (vm.leaderboard.count !== details.results.count) {
                            vm.showLeaderboardUpdate = true;
                        }
                    },
                    onError: function(response) {
                        var error = response.data;
                        utilities.storeData('emailError', error.detail);
                        $state.go('web.permission-denied');
                        vm.stopLoader();
                    }
                };
                utilities.sendRequest(parameters);
            }, 5000);
        };
```

```
 vm.leaderboard[i]['submission__submitted_at_formatted'] = vm.leaderboard[i]['submission__submitted_at'];
                        vm.initial_ranking[vm.leaderboard[i].id] = i+1;
                        var dateTimeNow = moment(new Date());
                        var submissionTime = moment(vm.leaderboard[i].submission__submitted_at);
                        var duration = moment.duration(dateTimeNow.diff(submissionTime));
                        if (duration._data.years != 0) {
                            var years = duration.asYears();
                            vm.leaderboard[i].submission__submitted_at = years;
                            if (years.toFixed(0)==1) {
                                vm.leaderboard[i].timeSpan = 'year';
                            } else {
                                vm.leaderboard[i].timeSpan= 'years';
                            }
                        }
                        else if (duration._data.months !=0) {
                            var months = duration.months();
                            vm.leaderboard[i].submission__submitted_at = months;
                            if (months.toFixed(0)==1) {
                                vm.leaderboard[i].timeSpan = 'month';
                            } else {
                                vm.leaderboard[i].timeSpan = 'months';
                            }
                        }
                        else if (duration._data.days !=0) {
                            var days = duration.asDays();
                            vm.leaderboard[i].submission__submitted_at = days;
                            if (days.toFixed(0)==1) {
                                vm.leaderboard[i].timeSpan = 'day';
                            } else {
                                vm.leaderboard[i].timeSpan = 'days';
                            }
                        }
                        else if (duration._data.hours !=0) {
                            var hours = duration.asHours();
                            vm.leaderboard[i].submission__submitted_at = hours;
                            if (hours.toFixed(0)==1) {
                                vm.leaderboard[i].timeSpan = 'hour';
                            } else {
                                vm.leaderboard[i].timeSpan = 'hours';
                            }                        
                        } 
                        else if (duration._data.minutes !=0) {
                            var minutes = duration.asMinutes();
                            vm.leaderboard[i].submission__submitted_at = minutes;
                            if (minutes.toFixed(0)==1) {
                                vm.leaderboard[i].timeSpan = 'minute';
                            } else {
                                vm.leaderboard[i].timeSpan = 'minutes';
                            }
                        }
                        else if (duration._data.seconds != 0) {
                            var second = duration.asSeconds();
                            vm.leaderboard[i].submission__submitted_at = second;
                            if (second.toFixed(0)==1) {
                                vm.leaderboard[i].timeSpan = 'second';
                            } else {
                                vm.leaderboard[i].timeSpan = 'seconds';
                            }
```

```
parameters.url = "jobs/challenge/" + vm.challengeId + "/challenge_phase/" + vm.phaseId + "/submission/?page=" + Math.ceil(vm.currentPage);
                    parameters.method = 'GET';
                    parameters.data = {};
                    parameters.callback = {
                        onSuccess: function(response) {
                            var details = response.data;
                            // Set the is_public flag corresponding to each submission
                            for (var i = 0; i < details.results.length; i++) {
                                vm.submissionVisibility[details.results[i].id] = details.results[i].is_public;
                                vm.baselineStatus[details.results[i].id] = details.results[i].is_baseline;
                            }
                            if (vm.submissionResult.results.length !== details.results.length) {
                                vm.showUpdate = true;
                            } else {
                                for (i = 0; i < details.results.length; i++) {
                                    if (details.results[i].status !== vm.submissionResult.results[i].status) {
                                        vm.showUpdate = true;
                                        break;
                                    }
                                }
                            }
                        },
                        onError: function(response) {
                            var error = response.data;
                            utilities.storeData('emailError', error.detail);
                            $state.go('web.permission-denied');
                            vm.stopLoader();
                        }
                    };
                    utilities.sendRequest(parameters);
                }, 5000);
            };
```

```
 var details = response.data;
                                vm.submissionResult = details;
                                // condition for pagination
                                if (vm.submissionResult.next === null) {
                                    vm.isNext = 'disabled';
                                    vm.currentPage = vm.submissionResult.count / 100;
                                } else {
                                    vm.isNext = '';
                                    vm.currentPage = parseInt(vm.submissionResult.next.split('page=')[1] - 1);
                                }
                                if (vm.submissionResult.previous === null) {
                                    vm.isPrev = 'disabled';
                                } else {
                                    vm.isPrev = '';
                                }
                                vm.stopLoader();
                            });
                        } else {
                            vm.stopLoader();
                        }
```

```
 submissionObject.classList = ['spin', 'progress-indicator'];
            parameters.url = 'jobs/submissions/' + submissionObject.id + '/re-run/';
            parameters.method = 'POST';
            parameters.token = userKey;
            parameters.callback = {
                onSuccess: function(response) {
                    $rootScope.notify("success", response.data.success);
                    submissionObject.classList = [''];
                },
                onError: function(response) {
                    var error = response.data;
                    $rootScope.notify("error", error);
                    submissionObject.classList = [''];
                }
            };
            utilities.sendRequest(parameters);
        };

```

```
  parameters.url = "challenges/challenge/create/challenge_phase_split/" + vm.phaseSplitId + "/";
            parameters.method = "PATCH";
            parameters.data = {
                "show_leaderboard_by_latest_submission": !vm.selectedPhaseSplit.show_leaderboard_by_latest_submission
            };
            parameters.callback = {
                onSuccess: function (response) {
                    vm.selectedPhaseSplit = response.data;
                    vm.getLeaderboard(vm.selectedPhaseSplit.id);
                    vm.sortLeaderboardTextOption = (vm.selectedPhaseSplit.show_leaderboard_by_latest_submission) ?
                        "Sort by best":"Sort by latest";
                },
                onError: function (response) {
                    var error = response.data;
                    vm.stopLoader();
                    $rootScope.notify("error", error);
                    return false;
                }
            };
            utilities.sendRequest(parameters);
        };
```

```
 vm.startLoader = loaderService.startLoader;
                        vm.startLoader("Loading Submissions");
                        if (url !== null) {
                            //store the header data in a variable
                            var headers = {
                                'Authorization': "Token " + userKey
                            };
                            //Add headers with in your request
                            $http.get(url, { headers: headers }).then(function(response) {
                                // reinitialized data
                                var details = response.data;
                                vm.submissionResult = details;
                                // condition for pagination
                                if (vm.submissionResult.next === null) {
                                    vm.isNext = 'disabled';
                                    vm.currentPage = vm.submissionResult.count / 100;
                                } else {
                                    vm.isNext = '';
                                    vm.currentPage = parseInt(vm.submissionResult.next.split('page=')[1] - 1);
                                }
                                if (vm.submissionResult.previous === null) {
                                    vm.isPrev = 'disabled';
                                } else {
                                    vm.isPrev = '';
                                }
                                vm.stopLoader();
                            });
                        } else {
                            vm.stopLoader();
                        }
```

```
 var status = response.status;
                    var message = "";
                    if(status === 200) {
                      var detail = response.data;
                      if (detail['is_public'] == true) {
                        message = "The submission is made public.";
                      }
                      else {
                        message = "The submission is made private.";
                      }
                      $rootScope.notify("success", message);
                    }
                },
```

```
 if (vm.phaseId) {
                parameters.url = "challenges/" + vm.challengeId + "/phase/" + vm.phaseId + "/download_all_submissions/" + vm.fileSelected + "/";
                if (vm.fieldsToGet === undefined || vm.fieldsToGet.length === 0) {
                    parameters.method = "GET";
                    parameters.callback = {
                        onSuccess: function(response) {
                            var details = response.data;
                            var anchor = angular.element('<a/>');
                            anchor.attr({
                                href: 'data:attachment/csv;charset=utf-8,' + encodeURI(details),
                                download: 'all_submissions.csv'
                            })[0].click();
                        },
                        onError: function(response) {
                            var details = response.data;
                            $rootScope.notify('error', details.error);
                        }
                    };
                    utilities.sendRequest(parameters);
                }
                else {
                    parameters.method = "POST";
                    var fieldsExport = [];
                    for(var i = 0 ; i < vm.fields.length ; i++) {
                        if (vm.fieldsToGet.includes(vm.fields[i].id)) {
                            fieldsExport.push(vm.fields[i].id);
                        }
                    }
                    parameters.data = fieldsExport;
                    parameters.callback = {
                        onSuccess: function(response) {
                            var details = response.data;
                            var anchor = angular.element('<a/>');
                            anchor.attr({
                                href: 'data:attachment/csv;charset=utf-8,' + encodeURI(details),
                                download: 'all_submissions.csv'
                            })[0].click();
                        },
                        onError: function(response) {
                            var details = response.data;
                            $rootScope.notify('error', details.error);
                        }
                    };
                    utilities.sendRequest(parameters);
                }
                
            } else {
                $rootScope.notify("error", "Please select a challenge phase!");
            }
        };
```

```
if (vm.submissionResult.results[i].id === submissionId) {
                    vm.submissionMetaData = vm.submissionResult.results[i];
                    break;
                }
```

```
parameters.url = "challenges/challenge_host_team/" + vm.page.creator.id + "/challenge/" + vm.page.id;
                parameters.method = 'PATCH';
                parameters.data = {
                    "published": !vm.isPublished,
                };
                vm.isPublished = !vm.isPublished;
                parameters.callback = {
                    onSuccess: function(response) {
                        var status = response.status;
                        if (status === 200) {
                            $mdDialog.hide();
                            $rootScope.notify("success", "The challenge was successfully made " + vm.toggleChallengeState);
                        }
                    },
                    onError: function(response) {
                        $mdDialog.hide();
                        vm.page.description = vm.tempDesc;
                        var error = response.data;
                        $rootScope.notify("error", error);
                    }
                };
                utilities.sendRequest(parameters);
            }, function() {
            // Nope
            });
        };
        // Edit Challenge Start and End Date
        vm.challengeDateDialog = function(ev) {
            vm.challengeStartDate = moment(vm.page.start_date);
            vm.challengeEndDate = moment(vm.page.end_date);
            $mdDialog.show({
                scope: $scope,
                preserveScope: true,
                targetEvent: ev,
                templateUrl: 'dist/views/web/challenge/edit-challenge/edit-challenge-date.html',
                escapeToClose: false
            });
        };
        vm.editChallengeDate = function(editChallengeDateForm) {
            if (editChallengeDateForm) {
                var challengeHostList = utilities.getData("challengeCreator");
                for (var challenge in challengeHostList) {
                    if (challenge == vm.challengeId) {
                        vm.challengeHostId = challengeHostList[challenge];
                        break;
                    }
                }
                parameters.url = "challenges/challenge_host_team/" + vm.challengeHostId + "/challenge/" + vm.challengeId;
                parameters.method = 'PATCH';
                if (new Date(vm.challengeStartDate).valueOf() < new Date(vm.challengeEndDate).valueOf()) {
                    parameters.data = {
                        "start_date": vm.challengeStartDate,
                        "end_date": vm.challengeEndDate
                    };
                    parameters.callback = {
                        onSuccess: function(response) {
                            var status = response.status;
                            utilities.hideLoader();
                            if (status === 200) {
                                vm.page.start_date = vm.challengeStartDate.format("MMM D, YYYY h:mm:ss A");
                                vm.page.end_date = vm.challengeEndDate.format("MMM D, YYYY h:mm:ss A");
                                $mdDialog.hide();
                                $rootScope.notify("success", "The challenge start and end date is successfully updated!");
                            }
                        },
                        onError: function(response) {
                            utilities.hideLoader();
                            $mdDialog.hide();
                            var error = response.data;
                            $rootScope.notify("error", error);
                        }
                    };
                    utilities.showLoader();
                    utilities.sendRequest(parameters);
                } else {
                    $rootScope.notify("error", "The challenge start date cannot be same or greater than end date.");
                }
            } else {
                $mdDialog.hide();
            }
        };
        $scope.$on('$destroy', function() {
            vm.stopFetchingSubmissions();
            vm.stopLeaderboard();
        });
        $rootScope.$on('$stateChangeStart', function() {
            vm.phase = {};
            vm.isResult = false;
            vm.stopFetchingSubmissions();
            vm.stopLeaderboard();
        });
```

```
 if (acceptTermsAndConditionsForm) {
                if (vm.termsAndConditions) {
                    vm.selectExistTeam();
                    $mdDialog.hide();
                }
            } else {
                $mdDialog.hide();
            }
        };
        
    }

```

</br>
</details>

### challengeHostTeamsCtrl.js

<details>
    <summary>View Code</summary>
    <br>

<br>Pagination for host teams</br>
```
 var details = response.data;
                                vm.existTeam = details;
                                // condition for pagination
                                if (vm.existTeam.next === null) {
                                    vm.isNext = 'disabled';
                                    vm.currentPage = vm.existTeam.count / 100;
                                } else {
                                    vm.isNext = '';
                                    vm.currentPage = parseInt(vm.existTeam.next.split('page=')[1] - 1);
                                }
                                if (vm.existTeam.previous === null) {
                                    vm.isPrev = 'disabled';
                                } else {
                                    vm.isPrev = '';
                                }
                                vm.stopLoader();
                            });
                        } else {
                            vm.stopLoader();
                        }
```
<br>Remove host team</br>
```
 vm.startLoader();
                var parameters = {};
                parameters.url = 'hosts/remove_self_from_challenge_host/' + hostTeamId;
                parameters.method = 'DELETE';
                parameters.data = {};
                parameters.token = userKey;
                parameters.callback = {
                    onSuccess: function() {
                        vm.team.error = false;
                        $rootScope.notify("info", "You have removed yourself successfully");
                        var parameters = {};
                        parameters.url = 'hosts/challenge_host_team/';
                        parameters.method = 'GET';
                        parameters.token = userKey;
                        parameters.callback = {
                            onSuccess: function(response) {
                                var status = response.status;
                                var details = response.data;
                                if (status == 200) {
                                    vm.existTeam = details;
                                    // condition for pagination
                                    if (vm.existTeam.next === null) {
                                        vm.isNext = 'disabled';
                                        vm.currentPage = vm.existTeam.count / 10;
                                    } else {
                                        vm.isNext = '';
                                        vm.currentPage = parseInt(vm.existTeam.next.split('page=')[1] - 1);
                                    }
                                    if (vm.existTeam.previous === null) {
                                        vm.isPrev = 'disabled';
                                    } else {
                                        vm.isPrev = '';
                                    }
                                    if (vm.existTeam.count === 0) {
                                        vm.showPagination = false;
                                        vm.paginationMsg = "No team exists for now, start by creating a new team!";
                                    } else {
                                        vm.showPagination = true;
                                        vm.paginationMsg = "";
                                    }
                                }
                                vm.stopLoader();
                            }
                        };
                        utilities.sendRequest(parameters);
                    },
                    onError: function() {
                        vm.stopLoader();
                        $rootScope.notify("error", "Couldn't remove you from the challenge");
                    }
                };
                utilities.sendRequest(parameters);
            }, function() {});
        };
```
<br>Inviting host team</br>
```
 var parameters = {};
                parameters.url = 'hosts/challenge_host_teams/' + hostTeamId + '/invite';
                parameters.method = 'POST';
                parameters.data = {
                    "email": result
                };
                parameters.token = userKey;
                parameters.callback = {
                    onSuccess: function() {
                        $rootScope.notify("success", parameters.data.email + " has been added successfully");
                    },
                    onError: function(response) {
                        var error = response.data.error;
                        $rootScope.notify("error", error);
                    }
                };
                utilities.sendRequest(parameters);
            });
        };
```

</br>
</details>


### featuredChallengeCtrl.js

<details>
    <summary>View Code</summary>
    <br>
<br>Submission time picker</br>

```
var dateTimeNow = moment(new Date());
                        var submissionTime = moment(vm.leaderboard[i].submission__submitted_at);
                        var duration = moment.duration(dateTimeNow.diff(submissionTime));
                        if (duration._data.years != 0) {
                            var years = duration.asYears();
                            vm.leaderboard[i].submission__submitted_at = years;
                            if (years.toFixed(0)==1) {
                                vm.leaderboard[i].timeSpan = 'year';
                            } else {
                                vm.leaderboard[i].timeSpan= 'years';
                            }
                        }
                        else if (duration._data.months !=0) {
                            var months = duration.months();
                            vm.leaderboard[i].submission__submitted_at = months;
                            if (months.toFixed(0)==1) {
                                vm.leaderboard[i].timeSpan = 'month';
                            } else {
                                vm.leaderboard[i].timeSpan = 'months';
                            }
                        }
                        else if (duration._data.days !=0) {
                            var days = duration.asDays();
                            vm.leaderboard[i].submission__submitted_at = days;
                            if (days.toFixed(0)==1) {
                                vm.leaderboard[i].timeSpan = 'day';
                            } else {
                                vm.leaderboard[i].timeSpan = 'days';
                            }
                        }
                        else if (duration._data.hours !=0) {
                            var hours = duration.asHours();
                            vm.leaderboard[i].submission__submitted_at = hours;
                            if (hours.toFixed(0)==1) {
                                vm.leaderboard[i].timeSpan = 'hour';
                            } else {
                                vm.leaderboard[i].timeSpan = 'hours';
                            }                        
                        } 
                        else if (duration._data.minutes !=0) {
                            var minutes = duration.asMinutes();
                            vm.leaderboard[i].submission__submitted_at = minutes;
                            if (minutes.toFixed(0)==1) {
                                vm.leaderboard[i].timeSpan = 'minute';
                            } else {
                                vm.leaderboard[i].timeSpan = 'minutes';
                            }
                        }
                        else if (duration._data.seconds != 0) {
                            var second = duration.asSeconds();
                            vm.leaderboard[i].submission__submitted_at = second;
                            if (second.toFixed(0)==1) {
                                vm.leaderboard[i].timeSpan = 'second';
                            } else {
                                vm.leaderboard[i].timeSpan = 'seconds';
                            }
                        }
                    }
                    
```

</br>
</details>


### teamsCtrl.js


<details>
    <summary>View Code</summary>
    <br>

<br>Pagination for team list</br>
```
 var details = response.data;
                                vm.existTeam = details;
                                // condition for pagination
                                if (vm.existTeam.next === null) {
                                    vm.isNext = 'disabled';
                                    vm.currentPage = vm.existTeam.count / 100;
                                } else {
                                    vm.isNext = '';
                                    vm.currentPage = parseInt(vm.existTeam.next.split('page=')[1] - 1);
                                }
                                if (vm.existTeam.previous === null) {
                                    vm.isPrev = 'disabled';
                                } else {
                                    vm.isPrev = '';
                                }
                                vm.stopLoader();
                            });
                        } else {
                            vm.stopLoader();
                        }
                    };

```
<br>Remove participation from a challenge</br>
```
$mdDialog.show(confirm).then(function() {
                vm.startLoader();
                var parameters = {};
                parameters.url = 'participants/remove_self_from_participant_team/' + participantTeamId;
                parameters.method = 'DELETE';
                parameters.data = {};
                parameters.token = userKey;
                parameters.callback = {
                    onSuccess: function() {
                        vm.team.error = false;
                        $rootScope.notify("info", "You have removed yourself successfully");
                        var parameters = {};
                        parameters.url = 'participants/participant_team';
                        parameters.method = 'GET';
                        parameters.token = userKey;
                        parameters.callback = {
                            onSuccess: function(response) {
                                var status = response.status;
                                var details = response.data;
                                if (status == 200) {
                                    vm.existTeam = details;
                                    // condition for pagination
                                    if (vm.existTeam.next === null) {
                                        vm.isNext = 'disabled';
                                        vm.currentPage = vm.existTeam.count / 10;
                                    } else {
                                        vm.isNext = '';
                                        vm.currentPage = parseInt(vm.existTeam.next.split('page=')[1] - 1);
                                    }
                                    if (vm.existTeam.previous === null) {
                                        vm.isPrev = 'disabled';
                                    } else {
                                        vm.isPrev = '';
                                    }
                                    if (vm.existTeam.count === 0) {
                                        vm.showPagination = false;
                                        vm.paginationMsg = "No team exists for now. Start by creating a new team!";
                                    } else {
                                        vm.showPagination = true;
                                        vm.paginationMsg = "";
                                    }
                                }
                                vm.stopLoader();
                            }
                        };
                        utilities.sendRequest(parameters);
                    },
                    onError: function(response) {
                        var error = response.data['error'];
                        vm.stopLoader();
                        $rootScope.notify("error", error);
                    }
                };
                utilities.sendRequest(parameters);
            }, function() {
            });
        };
```
```
var parameters = {};
                parameters.url = 'participants/participant_team/' + participantTeamId + '/invite';
                parameters.method = 'POST';
                parameters.data = {
                    "email": result
                };
                parameters.token = userKey;
                parameters.callback = {
                    onSuccess: function(response) {
                        var message = response.data['message'];
                        $rootScope.notify("success", message);
                    },
                    onError: function(response) {
                        var error = response.data['error'];
                        $rootScope.notify("error", error);
                    }
                };
                utilities.sendRequest(parameters);
            }, function() {
            });
```

</br>
</details>
</br>
</details>


#  scripts/workers : 42.96%

Many parts of the code have not been tested yet drastically reducing coverage
<details>
    <summary>View files</summary>

### remote_submission_worker.py


<details>
    <summary>View Code</summary>
    <br>

```
 try:
        response = requests.get(url)
    except Exception as e:
        logger.error("Failed to fetch file from {}, error {}".format(url, e))
        response = None
    if response and response.status_code == 200:
        with open(download_location, "wb") as f:
            f.write(response.content)
        # extract zip file
        zip_ref = zipfile.ZipFile(download_location, "r")
        zip_ref.extractall(extract_location)
        zip_ref.close()
        # delete zip file
        try:
            os.remove(download_location)
        except Exception as e:
            logger.error(
                "Failed to remove zip file {}, error {}".format(
                    download_location, e
                )
            )
            traceback.print_exc()
```
```
 create_dir_as_python_package(CHALLENGE_DATA_BASE_DIR)
    try:
        challenge = get_challenge_by_queue_name()
    except Exception:
        logger.exception(
            "Challenge with queue name %s does not exists" % (QUEUE_NAME)
        )
        raise
    challenge_pk = challenge.get("id")
    phases = get_challenge_phases_by_challenge_pk(challenge_pk)
    extract_challenge_data(challenge, phases)
```
```
 challenge_data_directory = CHALLENGE_DATA_DIR.format(
        challenge_id=challenge.get("id")
    )
    evaluation_script_url = challenge.get("evaluation_script")
    create_dir_as_python_package(challenge_data_directory)
    # set entry in map
    PHASE_ANNOTATION_FILE_NAME_MAP[challenge.get("id")] = {}
    challenge_zip_file = join(
        challenge_data_directory,
        "challenge_{}.zip".format(challenge.get("id")),
    )
    download_and_extract_zip_file(
        evaluation_script_url, challenge_zip_file, challenge_data_directory
    )
    phase_data_base_directory = PHASE_DATA_BASE_DIR.format(
        challenge_id=challenge.get("id")
    )
    create_dir(phase_data_base_directory)
    for phase in phases:
        phase_data_directory = PHASE_DATA_DIR.format(
            challenge_id=challenge.get("id"), phase_id=phase.get("id")
        )
        # create phase directory
        create_dir(phase_data_directory)
        annotation_file_url = phase.get("test_annotation")
        annotation_file_name = os.path.basename(phase.get("test_annotation"))
        PHASE_ANNOTATION_FILE_NAME_MAP[challenge.get("id")][
            phase.get("id")
        ] = annotation_file_name
        annotation_file_path = PHASE_ANNOTATION_FILE_PATH.format(
            challenge_id=challenge.get("id"),
            phase_id=phase.get("id"),
            annotation_file=annotation_file_name,
        )
        download_and_extract_file(annotation_file_url, annotation_file_path)
    try:
        # import the challenge after everything is finished
        challenge_module = importlib.import_module(
            CHALLENGE_IMPORT_STRING.format(challenge_id=challenge.get("id"))
        )
        EVALUATION_SCRIPTS[challenge.get("id")] = challenge_module
    except Exception:
        logger.exception(
            "Exception raised while creating Python module for challenge_id: %s"
            % (challenge.get("id"))
        )
        raise
def process_submission_callback(body):
    try:
        logger.info("[x] Received submission message %s" % body)
        process_submission_message(body)
    except Exception as e:
        logger.exception(
            "Exception while processing message from submission queue with error {}".format(
                e
            )
        )
def process_submission_message(message):
    """
    Extracts the submission related metadata from the message
    and send the submission object for evaluation
    """
    challenge_pk = int(message.get("challenge_pk"))
    phase_pk = message.get("phase_pk")
    submission_pk = message.get("submission_pk")
    submission_instance = extract_submission_data(submission_pk)
    # so that the further execution does not happen
    if not submission_instance:
        return
    challenge = get_challenge_by_queue_name()
    remote_evaluation = challenge.get("remote_evaluation")
    challenge_phase = get_challenge_phase_by_pk(challenge_pk, phase_pk)
    if not challenge_phase:
        logger.exception(
            "Challenge Phase {} does not exist for queue {}".format(
                phase_pk, QUEUE_NAME
            )
        )
        raise
    user_annotation_file_path = join(
        SUBMISSION_DATA_DIR.format(submission_id=submission_pk),
        os.path.basename(submission_instance.get("input_file")),
    )
    run_submission(
        challenge_pk,
        challenge_phase,
        submission_instance,
        user_annotation_file_path,
        remote_evaluation,
    )
def extract_submission_data(submission_pk):
    """
        * Expects submission id and extracts input file for it.
    """
    submission = get_submission_by_pk(submission_pk)
    if not submission:
        logger.critical("Submission {} does not exist".format(submission_pk))
        traceback.print_exc()
        # return from here so that the message can be acked
        # This also indicates that we don't want to take action
        # for message corresponding to which submission entry
        # does not exist
        return
    submission_input_file = submission.get("input_file")
    submission_data_directory = SUBMISSION_DATA_DIR.format(
        submission_id=submission.get("id")
    )
    submission_input_file_name = os.path.basename(submission_input_file)
    submission_input_file_path = SUBMISSION_INPUT_FILE_PATH.format(
        submission_id=submission.get("id"),
        input_file=submission_input_file_name,
    )
    create_dir_as_python_package(submission_data_directory)
    download_and_extract_file(
        submission_input_file, submission_input_file_path
    )
    return submission
```
```
except requests.exceptions.RequestException:
            logger.exception(
                "The worker is not able to establish connection with EvalAI due to {}"
                % (response.json())
            )
            raise
        except requests.exceptions.HTTPError:
            logger.exception(
                "The request to URL {} is failed due to {}"
                % (url, response.json())
            )
            raise
```
```
 except requests.exceptions.RequestException:
            logger.info(
                "The worker is not able to establish connection with EvalAI"
            )
            raise
```
```
  except requests.exceptions.RequestException:
            logger.exception(
                "The worker is not able to establish connection with EvalAI due to {}"
                % (response.json())
            )
            raise
        except requests.exceptions.HTTPError:
            logger.exception(
                "The request to URL {} is failed due to {}"
                % (url, response.json())
            )
            raise
```
```
 except requests.exceptions.RequestException:
            logger.info(
                "The worker is not able to establish connection with EvalAI"
            )
            raise
        except requests.exceptions.HTTPError:
            logger.info(
                "The request to URL {} is failed due to {}"
                % (url, response.json())
            )
            raise
```
```
 except requests.exceptions.RequestException:
            logger.info(
                "The worker is not able to establish connection with EvalAI"
            )
            raise
        except requests.exceptions.HTTPError:
            logger.info(
                "The request to URL {} is failed due to {}"
                % (url, response.json())
            )
            raise
```
```
def read_file_content(file_path):
    with open(file_path, "r") as obj:
        file_content = obj.read()
        if not file_content:
            file_content = " "
        return file_content
def run_submission(
    challenge_pk,
    challenge_phase,
    submission,
    user_annotation_file_path,
    remote_evaluation,
):
    """
    * Checks whether the corresponding evaluation script and the annotation file for the challenge exists or not
    * Calls evaluation script to evaluate the particular submission
    Arguments:
        challenge_pk  -- challenge Id in which the submission is created
        challenge_phase  -- challenge phase JSON object in which the submission is created
        submission  -- JSON object for the submisson
        user_annotation_file_path  -- File submitted by user as a submission
    """
    # Send the submission data to the evaluation script
    # so that challenge hosts can use data for webhooks or any other service.
    submission_output = None
    phase_pk = challenge_phase.get("id")
    submission_pk = submission.get("id")
    annotation_file_name = PHASE_ANNOTATION_FILE_NAME_MAP[challenge_pk][
        phase_pk
    ]
    annotation_file_path = PHASE_ANNOTATION_FILE_PATH.format(
        challenge_id=challenge_pk,
        phase_id=phase_pk,
        annotation_file=annotation_file_name,
    )
    submission_data_dir = SUBMISSION_DATA_DIR.format(
        submission_id=submission.get("id")
    )
    submission_data = {
        "submission_status": "running",
        "submission": submission_pk,
    }
    update_submission_status(submission_data, challenge_pk)
    status = "running"
    # create a temporary run directory under submission directory, so that
    # main directory does not gets polluted
    temp_run_dir = join(submission_data_dir, "run")
    create_dir(temp_run_dir)
    stdout_file = join(temp_run_dir, "temp_stdout.txt")
    stderr_file = join(temp_run_dir, "temp_stderr.txt")
    stdout = open(stdout_file, "a+")
    stderr = open(stderr_file, "a+")
    try:
        logger.info(
            "Sending submission {} for evaluation".format(submission_pk)
        )
        with stdout_redirect(stdout), stderr_redirect(stderr):
            submission_output = EVALUATION_SCRIPTS[challenge_pk].evaluate(
                annotation_file_path,
                user_annotation_file_path,
                challenge_phase.get("codename"),
                submission_metadata=submission,
            )
        if remote_evaluation:
            return
    except Exception:
        status = "failed"
        stderr.write(traceback.format_exc())
        stdout.close()
        stderr.close()
        stdout_content = read_file_content(stdout_file)
        stderr_content = read_file_content(stderr_file)
        submission_data = {
            "challenge_phase": phase_pk,
            "submission": submission_pk,
            "submission_status": status,
            "stdout": stdout_content,
            "stderr": stderr_content,
        }
        update_submission_data(submission_data, challenge_pk, submission_pk)
        shutil.rmtree(temp_run_dir)
        return
    stdout.close()
    stderr.close()
    stdout_content = read_file_content(stdout_file)
    stderr_content = read_file_content(stderr_file)
    submission_data = {
        "challenge_phase": phase_pk,
        "submission": submission_pk,
        "submission_status": status,
        "stdout": stdout_content,
        "stderr": stderr_content,
    }
    if "result" in submission_output:
        status = "finished"
        submission_data["result"] = json.dumps(submission_output.get("result"))
        submission_data["metadata"] = json.dumps(
            submission_output.get("submission_metadata")
        )
        submission_data["submission_status"] = status
    else:
        status = "failed"
        submission_data["submission_status"] = status
    update_submission_data(submission_data, challenge_pk, submission_pk)
    shutil.rmtree(temp_run_dir)
    return
def main():
    killer = GracefulKiller()
    logger.info(
        "Using {0} as temp directory to store data".format(BASE_TEMP_DIR)
    )
    create_dir_as_python_package(COMPUTE_DIRECTORY_PATH)
    sys.path.append(COMPUTE_DIRECTORY_PATH)
    # create submission base data directory
    create_dir_as_python_package(SUBMISSION_DATA_BASE_DIR)
    load_challenge()
    while True:
        logger.info(
            "Fetching new messages from the queue {}".format(QUEUE_NAME)
        )
        message = get_message_from_sqs_queue()
        message_body = message.get("body")
        if message_body:
            submission_pk = message_body.get("submission_pk")
            submission = get_submission_by_pk(submission_pk)
            if submission:
                if submission.get("status") == "finished":
                    message_receipt_handle = message.get("receipt_handle")
                    delete_message_from_sqs_queue(message_receipt_handle)
                elif submission.get("status") == "running":
                    continue
                else:
                    message_receipt_handle = message.get("receipt_handle")
                    logger.info(
                        "Processing message body: {}".format(message_body)
                    )
                    process_submission_callback(message_body)
                    # Let the queue know that the message is processed
                    delete_message_from_sqs_queue(message_receipt_handle)
        time.sleep(5)
        if killer.kill_now:
            break
if __name__ == "__main__":
    main()
    logger.info("Quitting Submission Worker.")
```

</br>
</details>


### submission_worker.py


<details>
    <summary>View Code</summary>
    <br>


```
evaluation_script_url = return_file_url_per_environment(
        evaluation_script_url
    )
    # create challenge directory as package
    create_dir_as_python_package(challenge_data_directory)
    # set entry in map
    PHASE_ANNOTATION_FILE_NAME_MAP[challenge.id] = {}
    challenge_zip_file = join(
        challenge_data_directory, "challenge_{}.zip".format(challenge.id)
    )
    download_and_extract_zip_file(
        evaluation_script_url, challenge_zip_file, challenge_data_directory
    )
    phase_data_base_directory = PHASE_DATA_BASE_DIR.format(
        challenge_id=challenge.id
    )
    create_dir(phase_data_base_directory)
    for phase in phases:
        phase_data_directory = PHASE_DATA_DIR.format(
            challenge_id=challenge.id, phase_id=phase.id
        )
        # create phase directory
        create_dir(phase_data_directory)
        annotation_file_url = phase.test_annotation.url
        annotation_file_url = return_file_url_per_environment(
            annotation_file_url
        )
        annotation_file_name = os.path.basename(phase.test_annotation.name)
        PHASE_ANNOTATION_FILE_NAME_MAP[challenge.id][
            phase.id
        ] = annotation_file_name
        annotation_file_path = PHASE_ANNOTATION_FILE_PATH.format(
            challenge_id=challenge.id,
            phase_id=phase.id,
            annotation_file=annotation_file_name,
        )
        download_and_extract_file(annotation_file_url, annotation_file_path)
    try:
        # import the challenge after everything is finished
        importlib.invalidate_caches()
        challenge_module = importlib.import_module(
            CHALLENGE_IMPORT_STRING.format(challenge_id=challenge.id)
        )
        EVALUATION_SCRIPTS[challenge.id] = challenge_module
    except Exception:
        logger.exception(
            "Exception raised while creating Python module for challenge_id: %s"
            % (challenge.id)
        )
        raise

```
```
 if remote_evaluation:
        try:
            logger.info(
                "Sending submission {} for remote evaluation".format(
                    submission.id
                )
            )
            with stdout_redirect(stdout) as new_stdout, stderr_redirect(
                stderr
            ) as new_stderr:
                submission_output = EVALUATION_SCRIPTS[challenge_id].evaluate(
                    annotation_file_path,
                    user_annotation_file_path,
                    challenge_phase.codename,
                    submission_metadata=submission_serializer.data,
                )
                return
        except Exception:
            stderr.write(traceback.format_exc())
            stderr.close()
            stdout.close()
            submission.status = Submission.FAILED
            submission.completed_at = timezone.now()
            submission.save()
            with open(stdout_file, "r") as stdout:
                stdout_content = stdout.read()
                submission.stdout_file.save(
                    "stdout.txt", ContentFile(stdout_content)
                )
            with open(stderr_file, "r") as stderr:
                stderr_content = stderr.read()
                submission.stderr_file.save(
                    "stderr.txt", ContentFile(stderr_content)
                )
            # delete the complete temp run directory
            shutil.rmtree(temp_run_dir)
            return
```
```
 try:
                    dataset_split = challenge_phase_split.dataset_split
                except Exception:
                    stderr.write(
                        "ORGINIAL EXCEPTION: The codename specified by your Challenge Host doesn't match"
                        " with that in the evaluation Script.\n"
                    )
                    stderr.write(traceback.format_exc())
                    successful_submission_flag = False
                    break
                leaderboard_data = LeaderboardData()
                leaderboard_data.challenge_phase_split = challenge_phase_split
                leaderboard_data.submission = submission
                leaderboard_data.leaderboard = (
                    challenge_phase_split.leaderboard
                )
                leaderboard_data.result = split_result.get(
                    dataset_split.codename
                )
                if "error" in submission_output:
                    leaderboard_data.error = error_bars_dict.get(
                        dataset_split.codename
                    )
                leaderboard_data_list.append(leaderboard_data)
            if successful_submission_flag:
                LeaderboardData.objects.bulk_create(leaderboard_data_list)
        # Once the submission_output is processed, then save the submission object with appropriate status
        else:
            successful_submission_flag = False
    except Exception:
        stderr.write(traceback.format_exc())
        successful_submission_flag = False
```
```
def process_add_challenge_message(message):
    challenge_id = message.get("challenge_id")
    try:
        challenge = Challenge.objects.get(id=challenge_id)
    except Challenge.DoesNotExist:
        logger.exception("Challenge {} does not exist".format(challenge_id))
    phases = challenge.challengephase_set.all()
    extract_challenge_data(challenge, phases)
```
```
def main():
    killer = GracefulKiller()
    logger.info(
        "Using {0} as temp directory to store data".format(BASE_TEMP_DIR)
    )
    create_dir_as_python_package(COMPUTE_DIRECTORY_PATH)
    sys.path.append(COMPUTE_DIRECTORY_PATH)
    q_params = {"approved_by_admin": True}
    q_params["start_date__lt"] = timezone.now()
    q_params["end_date__gt"] = timezone.now()
    challenge_pk = os.environ.get("CHALLENGE_PK")
    if challenge_pk:
        q_params["pk"] = challenge_pk
    if settings.DEBUG or settings.TEST:
        if eval(LIMIT_CONCURRENT_SUBMISSION_PROCESSING):
            if not challenge_pk:
                logger.exception(
                    "Please add CHALLENGE_PK for the challenge to be loaded in the docker.env file."
                )
                sys.exit(1)
            maximum_concurrent_submissions, challenge = load_challenge_and_return_max_submissions(
                q_params
            )
        else:
            challenges = Challenge.objects.filter(**q_params)
            for challenge in challenges:
                load_challenge(challenge)
    else:
        maximum_concurrent_submissions, challenge = load_challenge_and_return_max_submissions(
            q_params
        )
    # create submission base data directory
    create_dir_as_python_package(SUBMISSION_DATA_BASE_DIR)
    queue_name = os.environ.get("CHALLENGE_QUEUE", "evalai_submission_queue")
    queue = get_or_create_sqs_queue(queue_name)
    while True:
        for message in queue.receive_messages():
            if settings.DEBUG or settings.TEST:
                if eval(LIMIT_CONCURRENT_SUBMISSION_PROCESSING):
                    current_running_submissions_count = Submission.objects.filter(
                        challenge_phase__challenge=challenge.id,
                        status="running",
                    ).count()
                    if (
                        current_running_submissions_count
                        == maximum_concurrent_submissions
                    ):
                        pass
                    else:
                        logger.info(
                            "Processing message body: {0}".format(message.body)
                        )
                        process_submission_callback(message.body)
                        # Let the queue know that the message is processed
                        message.delete()
                else:
                    logger.info(
                        "Processing message body: {0}".format(message.body)
                    )
                    process_submission_callback(message.body)
                    # Let the queue know that the message is processed
                    message.delete()
            else:
                current_running_submissions_count = Submission.objects.filter(
                    challenge_phase__challenge=challenge.id, status="running"
                ).count()
                if (
                    current_running_submissions_count
                    == maximum_concurrent_submissions
                ):
                    pass
                else:
                    logger.info(
                        "Processing message body: {0}".format(message.body)
                    )
                    process_submission_callback(message.body)
                    # Let the queue know that the message is processed
                    message.delete()
        if killer.kill_now:
            break
        time.sleep(0.1)
if __name__ == "__main__":
    main()
    logger.info("Quitting Submission Worker.")
```


</br>
</details>


### worker_util.py


<details>
    <summary>View Code</summary>
    <br>


```
logger = logging.getLogger(__name__)
URLS = {
    "get_message_from_sqs_queue": "/api/jobs/challenge/queues/{}/",
    "delete_message_from_sqs_queue": "/api/jobs/queues/{}/receipt/{}/",
    "get_submission_by_pk": "/api/jobs/submission/{}",
    "get_challenge_phases_by_challenge_pk": "/api/challenges/{}/phases/",
    "get_challenge_by_queue_name": "/api/challenges/challenge/queues/{}/",
    "get_challenge_phase_by_pk": "/api/challenges/challenge/{}/challenge_phase/{}",
    "update_submission_data": "/api/jobs/challenge/{}/update_submission/",
}
class EvalAI_Interface:
    def __init__(self, AUTH_TOKEN, EVALAI_API_SERVER, QUEUE_NAME):
        self.AUTH_TOKEN = AUTH_TOKEN
        self.EVALAI_API_SERVER = EVALAI_API_SERVER
        self.QUEUE_NAME = QUEUE_NAME
    def get_request_headers(self):
        headers = {"Authorization": "Token {}".format(self.AUTH_TOKEN)}
        return headers
    def make_request(self, url, method, data=None):
        headers = self.get_request_headers()
        try:
            response = requests.request(
                method=method, url=url, headers=headers, data=data
            )
            response.raise_for_status()
        except requests.exceptions.RequestException:
            logger.info(
                "The worker is not able to establish connection with EvalAI"
            )
            raise
        return response.json()
    def return_url_per_environment(self, url):
        base_url = "{0}".format(self.EVALAI_API_SERVER)
        url = "{0}{1}".format(base_url, url)
        return url
    def get_message_from_sqs_queue(self):
        url = URLS.get("get_message_from_sqs_queue").format(self.QUEUE_NAME)
        url = self.return_url_per_environment(url)
        response = self.make_request(url, "GET")
        return response
    def delete_message_from_sqs_queue(self, receipt_handle):
        url = URLS.get("delete_message_from_sqs_queue").format(
            self.QUEUE_NAME, receipt_handle
        )
        url = self.return_url_per_environment(url)
        response = self.make_request(url, "GET")  # noqa
        return response.status_code
    def get_submission_by_pk(self, submission_pk):
        url = URLS.get("get_submission_by_pk").format(submission_pk)
        url = self.return_url_per_environment(url)
        response = self.make_request(url, "GET")
        return response
    def get_challenge_phases_by_challenge_pk(self, challenge_pk):
        url = URLS.get("get_challenge_phases_by_challenge_pk").format(
            challenge_pk
        )
        url = self.return_url_per_environment(url)
        response = self.make_request(url, "GET")
        return response
    def get_challenge_by_queue_name(self):
        url = URLS.get("get_challenge_by_queue_name").format(self.QUEUE_NAME)
        url = self.return_url_per_environment(url)
        response = self.make_request(url, "GET")
        return response
    def get_challenge_phase_by_pk(self, challenge_pk, challenge_phase_pk):
        url = URLS.get("get_challenge_phase_by_pk").format(
            challenge_pk, challenge_phase_pk
        )
        url = self.return_url_per_environment(url)
        response = self.make_request(url, "GET")
        return response
    def update_submission_data(self, data, challenge_pk, submission_pk):
        url = URLS.get("update_submission_data").format(challenge_pk)
        url = self.return_url_per_environment(url)
        response = self.make_request(url, "PUT", data=data)
        return response
    def update_submission_status(self, data, challenge_pk):
        url = "/api/jobs/challenge/{}/update_submission/".format(challenge_pk)
        url = self.return_url_per_environment(url)
        response = self.make_request(url, "PATCH", data=data)
        return response
```


</br>
</details>


### rl_submission_worker.py

<details>
    <summary>View Code</summary>
    <br>


```
class GracefulKiller:
    kill_now = False
    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)
    def exit_gracefully(self, signum, frame):
        self.kill_now = True
logger = logging.getLogger(__name__)
AUTH_TOKEN = os.environ.get("AUTH_TOKEN", "auth_token")
EVALAI_API_SERVER = os.environ.get(
    "EVALAI_API_SERVER", "http://localhost:8000"
)
QUEUE_NAME = os.environ.get("QUEUE_NAME", "evalai_submission_queue")
ENVIRONMENT_IMAGE = os.environ.get("ENVIRONMENT_IMAGE", "image_name:tag")
MESSAGE_FETCH_DEPLAY = int(os.environ.get("MESSAGE_FETCH_DEPLAY", "5"))
def create_deployment_object(image, submission, message):
    PYTHONUNBUFFERED_ENV = client.V1EnvVar(name="PYTHONUNBUFFERED", value="1")
    AUTH_TOKEN_ENV = client.V1EnvVar(name="AUTH_TOKEN", value=AUTH_TOKEN)
    EVALAI_API_SERVER_ENV = client.V1EnvVar(
        name="EVALAI_API_SERVER", value=EVALAI_API_SERVER
    )
    MESSAGE_BODY_ENV = client.V1EnvVar(name="BODY", value=str(message))
    agent_container = client.V1Container(
        name="agent", image=image, env=[PYTHONUNBUFFERED_ENV]
    )
    environment_container = client.V1Container(
        name="environment",
        image=ENVIRONMENT_IMAGE,
        env=[
            PYTHONUNBUFFERED_ENV,
            AUTH_TOKEN_ENV,
            EVALAI_API_SERVER_ENV,
            MESSAGE_BODY_ENV,
        ],
    )
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels={"app": "evaluation"}),
        spec=client.V1PodSpec(
            containers=[environment_container, agent_container]
        ),
    )
    spec = client.ExtensionsV1beta1DeploymentSpec(
        replicas=1, template=template
    )
    deployment = client.ExtensionsV1beta1Deployment(
        api_version="extensions/v1beta1",
        kind="Deployment",
        metadata=client.V1ObjectMeta(name="submission-{0}".format(submission)),
        spec=spec,
    )
    return deployment
def create_deployment(api_instance, deployment):
    api_response = api_instance.create_namespaced_deployment(
        body=deployment, namespace="default"
    )
    logger.info("Deployment created. status='%s'" % str(api_response.status))
def process_submission_callback(message, api):
    config.load_kube_config()
    extensions_v1beta1 = client.ExtensionsV1beta1Api()
    logger.info(message)
    submission_data = {
        "submission_status": "running",
        "submission": message["submission_pk"],
    }
    logger.info(submission_data)
    api.update_submission_status(submission_data, message["challenge_pk"])
    dep = create_deployment_object(
        message["submitted_image_uri"], message["submission_pk"], message
    )
    create_deployment(extensions_v1beta1, dep)
def main():
    api = EvalAI_Interface(
        AUTH_TOKEN=AUTH_TOKEN,
        EVALAI_API_SERVER=EVALAI_API_SERVER,
        QUEUE_NAME=QUEUE_NAME,
    )
    logger.info(
        "String RL Worker for {}".format(
            api.get_challenge_by_queue_name()["title"]
        )
    )
    killer = GracefulKiller()
    while True:
        logger.info(
            "Fetching new messages from the queue {}".format(QUEUE_NAME)
        )
        message = api.get_message_from_sqs_queue()
        logger.info(message)
        message_body = message.get("body")
        if message_body:
            submission_pk = message_body.get("submission_pk")
            submission = api.get_submission_by_pk(submission_pk)
            if submission:
                if submission.get("status") == "finished":
                    message_receipt_handle = message.get("receipt_handle")
                    api.delete_message_from_sqs_queue(message_receipt_handle)
                elif submission.get("status") == "running":
                    continue
                else:
                    message_receipt_handle = message.get("receipt_handle")
                    logger.info(
                        "Processing message body: {}".format(message_body)
                    )
                    process_submission_callback(message_body, api)
                    api.delete_message_from_sqs_queue(
                        message.get("receipt_handle")
                    )
        time.sleep(MESSAGE_FETCH_DEPLAY)
        if killer.kill_now:
            break
if __name__ == "__main__":
    main()
    logger.info("Quitting Submission Worker.")
```

</br>
</details>
</br>
</details>

# manage.py : 0%
None of the code is tested yet


