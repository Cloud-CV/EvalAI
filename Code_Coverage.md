# CODE COVERAGE
### The part of files/code listed below is not tested and  is responsible for lower Code Coverage of EvaliAi.
### *The Small Discription given above each code piece is from the comments and my own basic understanding and can be wrong.
&nbsp;
# Front-End
&nbsp;
## challengeCtrl.js
&nbsp;
### 1. This Code(From line 75 till 82) is checking for unique rank number from the url & if exists hightlight the entry. It is a part of function ChallengeCtrl. 
```
 $timeout(function() {
                var elementId = $location.absUrl().split('?')[0].split('#')[1];
                if (elementId) {
                    $anchorScroll.yOffset = 90;
                    $anchorScroll(elementId);
                    $scope.isHighlight = elementId.split("leaderboardrank-")[1];
                }
            }
```
## 2.(From line 86 to 95) It scroll to the specific entry of the leaderboard.
```
vm.scrollToSpecificEntryLeaderboard = function (elementId) {
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
## 3.(From line 365 to 403) The function check for many thing like partication state ,challenge host list and wheather challenge registrations are open or not. 
```
vm.toggleParticipation = function (ev, isRegistrationOpen) {
            // ev.stopPropagation();
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
## 4.(From line 424 to 433) It is a part of function named isSubmissionUsingUrl and is checking for submission url format which include checking for extension also.
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
                        }
```
## 5.(From line 602 to 625) The function is responsible to Get the leaderboard view.
```
vm.startLeaderboard = function() {
            vm.stopLeaderboard();
            vm.poller = $interval(function() {
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
## 6.(From line 671 to 727) It is the part of the function which is responsible to show leaderboard.
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
                        }
                    }
```
## 7.(From line 762 to 775) Set the is_public flag corresponding to each submission
```
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
```
## 8.(From line 901 to 922) Reinitialize data and Set condition for pagination.
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
## 9.(From line 1005 to 1022) A function to attemp submission again.
```
 vm.reRunSubmission = function(submissionObject) {
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
## 10.(From line 1047 to 1068) A function to tongle or change leaderboard by latest category
```
vm.toggleShowLeaderboardByLatest = function() {
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
## 11.(From line 1257 to 1268) Tell wheather the submission is public or private or other.
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
```
##  12.(From line 1406 to 1454) To Download the Submission.
```
 vm.downloadChallengeSubmissions = function() {
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
           
```
## 13.(From line 2024 to 2064) A Function to edit the challeng starting and ending time.
```
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

```
&nbsp;
## teamsCtrl.js
## 1.(From line 258 to 325) Notify about the action done on participant team and condition of pagination
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
## 2.(From line 340 to 362) Display success or error message.
```
 $mdDialog.show(confirm).then(function(result) {
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
        };
```
&nbsp;
## challengeHostTeamsCtrl.js
## 1.(From line 258 to 325) Notify about the action done on host team and condition of pagination
```
$mdDialog.show(confirm).then(function() {
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
## 2.(From line 402 to 421) To Show wheather email have been successfully added or not
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
&nbsp;
# Scripts

## Remote_submission_worker.py

## 1.(From line 99 to 113) Function to extract download a file. download_location` should include name of file as well.
```
def download_and_extract_file(url, download_location):
    try:
        response = requests.get(url)
    except Exception as e:
        logger.error("Failed to fetch file from {}, error {}".format(url, e))
        traceback.print_exc()
        response = None
    if response and response.status_code == 200:
        with open(download_location, "wb") as f:
            f.write(response.content)
```
## 2.(From line 116 to 143) Function to extract download a zip file, extract it and then removes the zip file.download_location` should include name of file as well.
```
def download_and_extract_zip_file(url, download_location, extract_location):
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
## 3.(From line 172 to 187) Creates python package for a challenge and extracts relevant data.
```
def load_challenge():
    """
        Creates python package for a challenge and extracts relevant data
    """
    # make sure that the challenge base directory exists
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
## 4.(From line 190 to 245) Expects a challenge object and an array of phase object. Extracts `evaluation_script` for challenge and `annotation_file` for each phase
```
def extract_challenge_data(challenge, phases):
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
```
## 5.(From line 248 to 253) 
```
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
```
## 6.(From line 260 to 293) Extracts the submission related metadata from the message and send the submission object for evaluation
```
def process_submission_message(message):
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
```
&nbsp;
## Submission_worker.py

## 1.(From line 133 to 162) * Function to extract download a zip file, extract it and then removes the zip file.`download_location` should include name of file as well.
```
def download_and_extract_zip_file(url, download_location, extract_location):
    try:
        response = requests.get(url, stream=True)
    except Exception as e:
        logger.error("Failed to fetch file from {}, error {}".format(url, e))
        response = None
    if response and response.status_code == 200:
        with open(download_location, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
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
## 2.(From line 197 to 262)  * Expects a challenge object and an array of phase object. Extracts `evaluation_script` for challenge and `annotation_file` for each phase
```
ef extract_challenge_data(challenge, phases):
    challenge_data_directory = CHALLENGE_DATA_DIR.format(
        challenge_id=challenge.id
    )
    evaluation_script_url = challenge.evaluation_script.url
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
## 3.(From line 587 to 596)
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
# File rl_submission_worker.py and worker_util.py have no test written So it have 0% Coverage.
&nbsp;
# Apps/base
&nbsp;
# Files apps.py and management/commands/seed.py have no test written So it have 0% Coverage.
&nbsp;
## utils.py
## 1.(From line 72 to 79) Turn `data` into a hash and an encoded string, suitable for use with `decode_data`.
```
def encode_data(data):
    encoded = []
    for i in data:
        encoded.append(base64.encodestring(i).split("=")[0])
    return encoded
```
## 2.(From line 86 to 89) The inverse of `encode_data`.
```
def decode_data(data):
    decoded = []
    for i in data:
        decoded.append(base64.decodestring(i + "=="))
    return decoded
```
## 3.(From line 92 to 124) Function to send email.
```
def send_email(
    sender=settings.CLOUDCV_TEAM_EMAIL,
    recepient=None,
    template_id=None,
    template_data={},
):
    """Keyword Arguments:
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
```
## 4.(From line 127 to 133) Get Url from Host.
```
def get_url_from_hostname(hostname):
    if settings.DEBUG or settings.TEST:
        scheme = "http"
    else:
        scheme = "https"
    url = "{}://{}".format(scheme, hostname)
    return url
```
## 5.(From lne 157 to 184) Check if the queue exists. If no, then create one
```
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
&nbsp;
# Jobs
# File apps.py  have no test written So it have 0% Coverage.
#  utils.py

## 1.(From line 74 to 94) Check for monthy submission limit
```
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
## 2.(From line 140 to 152) Checks that a given URL is reachable.
```
def is_url_valid(url):
    """
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
```
## 3.(From line 158 to 170)Get file object from a url 
```
def get_file_from_url(url):
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
&nbsp;
# tasks.py
## 1.(From line 23 to line 83) Download submission file from url and send it for the evaluation
```
def download_file_and_publish_submission_message(
    request_data,
    user_pk,
    request_method,
    challenge_phase_id
):
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
&nbsp;
# Base
# Utils.py
## 1.(From line 72 to 79) Turns `data` into a hash and an encoded string, suitable for use with `decode_data`.
```
def encode_data(data):
    encoded = []
    for i in data:
        encoded.append(base64.encodestring(i).split("=")[0])
    return encoded
```
## 2.(From line 82 to 89) The inverse of `encode_data`.
```
def decode_data(data):
    decoded = []
    for i in data:
        decoded.append(base64.decodestring(i + "=="))
    return decoded
```
## 3.(From line 92 to 124) Function to send email.
```
def send_email(
    sender=settings.CLOUDCV_TEAM_EMAIL,
    recepient=None,
    template_id=None,
    template_data={},
):
    """
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
```
## 4.(From line 157 to 184) Check if the queue exists. If no, then create one
```
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

# These are all the file/piece for which Test are not written and is decreasing evalai coverage below 90%.