Code Coverage Analysis
======================

*Every file has two section. A code snippet section which is directly taken from codecov codebase. There is also another 
section which takes care of specific functions which dont have testing code. The description of functions and missing test cases
are according to my understanding of the code and may not be 100% fool proof*

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
    Turn `data` into a hash and an encoded string, suitable for use with `decode_data`.<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/apps/base/utils.py#L72
    <br>
    2)def decode_data(data)<br>
    The inverse of `encode_data`.<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/apps/base/utils.py#L82
    <br>
    3)send_email :<br>
    Function to send email<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/apps/base/utils.py#L92
    <br>
    4)get_url_from_hostname(hostname) <br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/apps/base/utils.py#L127
    <br>
    5)get_or_create_sqs_queue_object<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/apps/base/utils.py#L157
    <br>
    6)send_slack_notification<br>
    Exception raised while sending slack notification<br>
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
    1)start_selected_workers :<br>
    message to display successful or unsuccessful start of selected workers<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/apps/challenges/admin.py#L73<br>
    2)stop_selected_workers : <br>
    message to display successful or unsuccessful stop of selected workers<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/apps/challenges/admin.py#L96<br>
    3)scale_selected_workers :<br>
    message to display successful or unsuccessful scale of selected workers<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/apps/challenges/admin.py#L119<br>
    4)restart_selected_workers :<br>
    message to display successful or unsuccessful restart of selected workers<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/apps/challenges/admin.py#L152<br>
    5)delete_selected_workers :<br>
    message to display successful or unsuccessful delete of selected workers<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/apps/challenges/admin.py#L177 <br>
    
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
</details>



### tasks.py

A look at the file is required since the coverage is extremely low and none of it is tested



### utils.py

<details>
    <summary>View missing test cases</summary>
    <br>
    1)get_remaining_submission_for_a_phase<br>
    response messages are not tested. Monthly submission limit check for time and date is not tested.<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/apps/jobs/utils.py#L74<br>
    2)is_url_valid:<br>
     Checks that a given URL is reachable<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/apps/jobs/utils.py#L140<br>
    3)get_file_from_url<br>
    Get file object from a url
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
developer settings to be used do not have test code<br>
https://codecov.io/gh/Cloud-CV/EvalAI/src/master/evalai/celery.py#L9<br>
</details>

### urls.py

<details>
    <summary>View missing test cases</summary>
    <br>
 URLs pattern test for debug mode<br>
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
    1) onSuccess: function(response)<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/analyticsCtrl.js#L144<br>
    2) navigate to permissions denied page<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/analyticsCtrl.js#L161    <br>
    3) & 4) Similar at https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/analyticsCtrl.js#L184 & https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/analyticsCtrl.js#L200<br>
    5)vm.downloadChallengeParticipantTeams = function()<br>
    Response OnSuccess and OnError response ; Getting participants of a specific challenge ID<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/analyticsCtrl.js#L236<br>
</details>


### authCtrl.js

<details>
    <summary>View missing test cases</summary>
    <br>
    1) toggle password visibility<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/authCtrl.js#L58<br>
    2) toggle confirm password visibility<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/authCtrl.js#L64<br>
    3)parameters.callback<br>
    Check for different fields in webpage if valid or not. eg email, password etc. and show message "vm.regMsg = "Registered   <br>     
    successfully, Login to continue!";" via vm.regmsg <br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/authCtrl.js#L101<br>
    5)parameters.callback<br>
    Process user info and change the state accorddingly and message generation<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/authCtrl.js#L163<br>
    6)Check password strength<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/authCtrl.js#L200<br>
    7) New password function<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/authCtrl.js#L282<br>
</details>
    


### challengeCtrl.js

<details>
    <summary>View missing test cases</summary>
    <br>
    1) timeout function for " get unique rank number from the url & if exists hightlight the entry".<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/challengeCtrl.js#L76<br>
    2)scroll to the specific entry of the leaderboard<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/challengeCtrl.js#L87<br>
    3)Error message while pagination when no teams are left<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/challengeCtrl.js#L222<br>
    4)vm.existTeam = details;<br>
    reinitialized data<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/challengeCtrl.js#L304<br>
    5) if (vm.existTeam.next === null)<br>
    condition for pagination<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/challengeCtrl.js#L308<br>
    6) ev.stopPropagation(); partivipate in a competition promt and follow messages.<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/challengeCtrl.js#L365<br>
    7) vm.startLoader("Making Submission")<br>
    Checks if url for submission is valid and submission<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/challengeCtrl.js#L424<br>
    8)set the result display to true or false depending on the fact if it is private or public<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/challengeCtrl.js#L512<br>
    9)vm.stopLeaderboard()<br>
    display my submissions call function.<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/challengeCtrl.js#L605<br>
    10)vm.leaderboard = {};<br>
    Show leaderboard with respect to latest time stamp it has eg: hours, days etc.<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/challengeCtrl.js#L671<br>
    11)vm.poller = $interval(function()<br>
    long polling (5s) for leaderboard<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/challengeCtrl.js#L755<br>
    12) $http.get(url, { headers: headers }).then(function(response)<br>
    reinitialized data<br>
    condition for pagination<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/challengeCtrl.js#L901<br>
    13)vm.reRunSubmission = function(submissionObject)<br>
    response message for submission <br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/challengeCtrl.js#L1006<br>
    14) vm.toggleShowLeaderboardByLatest = function()<br>
    sort leaderboard by latest to oldest<br>
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
   18)Confirm the state of the challenge, and then a message confirming it<br>
   https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/challengeCtrl.js#L1980<br>
   19)Edit Challenge Start and End Date<br>
   https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/challengeCtrl.js#L2011<br>
   20) vm.challengeDateDialog = function(ev)<br>
   Edit Challenge Start and End Date<br>
   https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/challengeCtrl.js#L2022<br>
   21) vm.editChallengeDate<br>
   The whole Function is missing test cases<br>
   https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/challengeCtrl.js#L2023<br>
   22)vm.acceptTermsAndConditions<br>
   Accepting terms and conditions and changing states accordingly.<br>
   https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/challengeCtrl.js#L2092<br>
     
    
</details>



### challengeHostTeamsCtrl.js

<details>
    <summary>View missing test cases</summary>
    <br>
    1)Test for turning pagination off when no teams more teams exist.<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/challengeHostTeamsCtrl.js#L72<br>
    2)Test for reinitializing data and checking condition for pagination when displaying teams.<br>
    https://codecov.io/gh/Cloud-CV/EvalAI/src/master/frontend/src/js/controllers/challengeHostTeamsCtrl.js#L119<br>
    3) $mdDialog.show(confirm).then(function()<br>
    Display dialogue box for various purposes<br>
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
    getting challenge message if successful or not2<br>
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


