Code Coverage Analysis
======================

*Every file has a section which takes care of specific functions which dont have testing code. The description of functions and missing test cases are according to my understanding of the code and may not be 100% fool proof*

# Apps : 77.89%

<details>
    <summary>View Files</summary>
    <br>
    
## base

### Utils.py 

<details>
    <summary>View missing test cases</summary> 
    </br>
    1)def encode_data(data) : <br>
    Turn a test `data` into a hash and an encoded string, suitable for use with `decode_data`.<br>
    def decode_data(data)<br>
    then use The inverse of `encode_data` to find if the test was successfully carried 
    out or not.<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/apps/base/utils.py#L72
    <br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/apps/base/utils.py#L82
    <br>
    3)send_email :<br>
    Test to confirm if the send email function was performed correctly<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/apps/base/utils.py#L92
    <br>
    4)get_url_from_hostname(hostname) <br>
    Test to check if the url is https or http when the developer mode has been switched off and on respectively.<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/apps/base/utils.py#L127
    <br>
    5)get_or_create_sqs_queue_object<br>
    Test to check if queue evalai_submission_queue is created or not.A blank queue can be used for testing.<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/apps/base/utils.py#L157
    <br>
    6)send_slack_notification<br>
    To test that when exception is raised a slack notification is sent or not<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/apps/base/utils.py#L222
    
</details>    



### management/commands/seed.py

This file does'nt has any test cases.



### apps.py

This file does'nt has any test cases.


## challenges

### admin

<details>
    <summary>View missing test cases</summary>
    <br>
    1)Test to check if the selected_workers have carried out their operations successfully, that is, to, start, stop, scale,
    restart and delete. To check if the corresponding messages are displayed correctly of not.</br>
    start_selected_workers :<br>
    message to display successful or unsuccessful start of selected workers<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/apps/challenges/admin.py#L73<br>
    )stop_selected_workers : <br>
    message to display successful or unsuccessful stop of selected workers<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/apps/challenges/admin.py#L96<br>
    )scale_selected_workers :<br>
    message to display successful or unsuccessful scale of selected workers<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/apps/challenges/admin.py#L119<br>
    )restart_selected_workers :<br>
    message to display successful or unsuccessful restart of selected workers<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/apps/challenges/admin.py#L152<br>
    )delete_selected_workers :<br>
    message to display successful or unsuccessful delete of selected workers<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/apps/challenges/admin.py#L177 <br>
    2)Test to check if the returned value of challenge name corresponding to phase-split is correct or not.<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/apps/challenges/admin.py#L259
    Similar tests required to check returned values for<br>
    >challenge name and id for a challenge<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/apps/challenges/admin.py#L328<br>
    >username and id of a user<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/apps/challenges/admin.py#L335<br>
    >the host team name and the member name<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/apps/challenges/admin.py#L342<br>
    >challenge name corresponding to leaderboard data entry<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/apps/challenges/admin.py#L300<br>
    >challenge name corresponding to phase<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/apps/challenges/admin.py#L233<br>
    
</details>    
    


### apps.py

This file does'nt has any test cases.


### aws_utils.py

The coverage is extremely low and therefore the whole file must be considered for testing.
 

## jobs

<details>
    <summary>View Files</summary>
    <br>
    
### sender.py
<details>
    <summary>View missing test cases</summary>
    <br>
    1)publish_submission_message<br>
    Display error message<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/apps/jobs/sender.py#L73<br>
    2) similar queue start test as " Test to check if queue evalai_submission_queue is created or not"
    A blank queue can be used for testing.<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/apps/jobs/sender.py#L42
    
</details>



### tasks.py

A look at the file is required since the coverage is extremely low and none of it is tested



### utils.py

<details>
    <summary>View missing test cases</summary>
    <br>
    1)get_remaining_submission_for_a_phase<br>
    response messages are not tested. Monthly submission limit check for time and date is not tested.<br>
    if submissions_done_today_count >= max_submissions_per_day_count, to make a test for blank submissions and test out diffrent outputs 
    and messages.
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/apps/jobs/utils.py#L74<br>
    2)is_url_valid:<br>
    Test to check urllib.request.Request is working properly(url)<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/apps/jobs/utils.py#L140<br>
    3)get_file_from_url<br>
    Test for proper download of a file from a url. A blank file may be used from a specific test url
    to do so.
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/apps/jobs/utils.py#L155<br>
    
</details>


</br>
</details>
</br>
</details>


# Evalai : 72.22%
<details>
    <summary>View Files</summary>
    <br>
    
### celery.py

<details>
    <summary>View missing test cases</summary>
    <br>
celery_dev does not have test code<br>
Check for this app.conf.task_default_queue = 'celery_dev' when developers setting is  enabled<br>
https://codecov.io/gh/Cloud-CV/EvalAI/src/master/evalai/celery.py#L9<br>
</details>

### urls.py

<details>
    <summary>View missing test cases</summary>
    <br>
 Test for  adding " urlpatterns += "<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/evalai/urls.py#L99
</details>


</br>
</details>

# Controllers : 78.77%

<details>
    <summary>View Files</summary>
    <br>

### analyticsCtrl.js

<details>
    <summary>View missing test cases</summary>
    <br>
    1) onSuccess: function(response)
    <br>
    Test to check if this function is working properly "  if (challengePhaseId[i] == response.data.challenge_phase)"<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/analyticsCtrl.js#L144<br>
    2) navigate to permissions denied page<br>
    Test navigation to permission denied page<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/analyticsCtrl.js#L161    <br>
    3) & 4) Similar at https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/analyticsCtrl.js#L184 & https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/analyticsCtrl.js#L200<br>
    5)vm.downloadChallengeParticipantTeams = function()<br>
    Response OnSuccess and OnError response ; Getting participants of a specific challenge ID<br>
    We need a test case which will ensure the download of CSV file.<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/analyticsCtrl.js#L236<br>
</details>


### authCtrl.js

<details>
    <summary>View missing test cases</summary>
    <br>
    1)Test to ensure that password's visibility has been toggled<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/authCtrl.js#L58<br>
    2)Test to ensure that confirm password's visibility has been toggled<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/authCtrl.js#L64<br>
    3)parameters.callback<br>
    Test to check for different diversity of field in webpage and
    respective forwarding of state. eg email, password etc. and show message "vm.regMsg = "Registered   <br>     
    successfully, Login to continue!";" via vm.regmsg <br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/authCtrl.js#L101<br>
    5)parameters.callback<br>
    Cross the list, is fields are "'undefined' ? true : false" Process user info and change the state accorddingly
    and message generation<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/authCtrl.js#L163<br>
    6)Test to check if password strength is correctly displayed<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/authCtrl.js#L200<br>
    7) Test for reset password function error<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/authCtrl.js#L282<br>
</details>
    


### challengeCtrl.js

<details>
    <summary>View missing test cases</summary>
    <br>
    1) Test for " get unique rank number from the url & if exists hightlight the entry" by using a test string and highlighting for
    testing purposes.<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/challengeCtrl.js#L76<br>
    2)Test for $location, $scroll and $anchor<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/challengeCtrl.js#L87<br>
    3)Test for onerror pagination message<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/challengeCtrl.js#L222<br>
    4)All functions related to pagination must be tested<br>
    reinitialized data<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/challengeCtrl.js#L304<br>
    >) if (vm.existTeam.next === null)<br>
    condition for pagination<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/challengeCtrl.js#L308<br>
    6) ev.stopPropagation(); Test for participation in a competition promt and follow messages.<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/challengeCtrl.js#L365<br>
    7) vm.startLoader("Making Submission")<br>
    Test a url for submission<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/challengeCtrl.js#L424<br>
    8)set a test result display to true or false depending on the fact if it is private or public<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/challengeCtrl.js#L512<br>
    9)vm.stopLeaderboard()<br>
    Test for displaying blank or test submission; call function.<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/challengeCtrl.js#L605<br>
    10)vm.leaderboard = {};<br>
    Show a test leaderboard with respect to latest time stamp it has eg: hours, days etc.<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/challengeCtrl.js#L671<br>
    11)vm.poller = $interval(function()<br>
    long polling (5s) for leaderboard<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/challengeCtrl.js#L755<br>
    12) $http.get(url, { headers: headers }).then(function(response)<br>
    reinitialized data<br>
    condition for pagination<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/challengeCtrl.js#L901<br>
    13)vm.reRunSubmission = function(submissionObject)<br>
    response message for a test submission <br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/challengeCtrl.js#L1006<br>
    14) vm.toggleShowLeaderboardByLatest = function()<br>
    sort leaderboard by latest to oldest for a test submission set<br>
    response message<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/challengeCtrl.js#L1048<br>
    15)vm.load = function(url)<br>
    A good description already present at the code<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/challengeCtrl.js#L1202<br>
    16)vm.downloadChallengeSubmissions = function()<br>
    Download submission; check for validity of phase id; <br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/challengeCtrl.js#L1407<br>
    17)Multiple occurance of<br>
    
        ```
             if (challenge == vm.challengeId) {
                                vm.challengeHostId = challengeHostList[challenge];
                                break;
       ```
   <br>
   18)Test the state of the challenge, followed by the valid message confirming it<br>
   https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/challengeCtrl.js#L1980<br>
   19)Test to verify a change in Challenge Start and End Date<br>
   https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/challengeCtrl.js#L2011<br>
   20) vm.challengeDateDialog = function(ev)<br>
   Test to edit Challenge Start and End Date<br>
   https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/challengeCtrl.js#L2022<br>
   21) vm.editChallengeDate<br>
   The whole Function is missing test cases<br>
   https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/challengeCtrl.js#L2023<br>
   22)vm.acceptTermsAndConditions<br>
   Test for changing states when Accepting terms and conditions.<br>
   https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/challengeCtrl.js#L2092<br>
     
    
</details>



### challengeHostTeamsCtrl.js

<details>
    <summary>View missing test cases</summary>
    <br>
    1)Test for pagination "off" when no dummy teams exist in the list.<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/challengeHostTeamsCtrl.js#L72<br>
    2)Test for reinitializing data and checking condition for pagination when displaying teams.<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/challengeHostTeamsCtrl.js#L119<br>
    3) $mdDialog.show(confirm).then(function()<br>
    Test : Display dialogue box for various purposes<br>
        >Remove self from challenge<br>
        >condition for pagination of teams<br>
        >removing self from challenge<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/challengeHostTeamsCtrl.js#L323<br>
    4) $mdDialog.show(confirm).then(function(result)<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/challengeHostTeamsCtrl.js#L400<br>
    

</details>




### featuredChallengeCtrl.js

<details>
    <summary>View missing test cases</summary>
    <br>
    1)onSuccess: function(response)<br>
    Test for arranging leaderboard according to timespan.<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/featuredChallengeCtrl.js#L133<br>
    
</details>



### teamsCtrl.js

<details>
    <summary>View missing test cases</summary>
    <br>
    Exactly same like challengeHostTeamsCtrl.js
    
</details>


</br>
</details>


#  Workers : 42.96%


<details>
    <summary>View files</summary>

### remote_submission_worker.py

This file is extremely low on coverage and hence a thorough look is required at the file itself.




### submission_worker.py

<details>
    <summary>View missing test cases</summary>
    <br>
    1)def __init__(self)<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/scripts/workers/submission_worker.py#L83<br>
    2)def exit_gracefully(self, signum, frame)<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/scripts/workers/submission_worker.py#L87<br>
    3)def alarm_handler(signum, frame)<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/scripts/workers/submission_worker.py#L89<br>
    4) evaluation_script_url = challenge.evaluation_script.url<br>
    Missing test casses are as follows<br>
    >create challenge directory as package<br>
    >set entry in map<br>
    >create phase directory<br>
    >import the challenge after everything is finished<br>
    Please take a look at the code link as the code has a very good documentation for the function itself<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/scripts/workers/submission_worker.py#L229<br>
    5)def load_challenge(challenge)<br>
    test for Creating python package for a challenge and extracting relevant data<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/scripts/workers/submission_worker.py#L287<br>
    6)remote_evaluation = submission.challenge_phase.challenge.remote_evaluation<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/scripts/workers/submission_worker.py#L380<br>
    7)Test for "Check if the dataset_split exists for the codename in the result"<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/scripts/workers/submission_worker.py#L488<br>
    8)def process_add_challenge_message(message)<br>
    Test for getting challenge message if successful or not<br>
    9)def main():<br>
    This whole function does not contain any test code<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/scripts/workers/submission_worker.py#L693<br>
    
</details>




### worker_util.py

It is used to update submission



### rl_submission_worker.py

No testing code available at all



### worker_util.py
No testing code available

</details>

# manage.py : 0%
No testing code available


