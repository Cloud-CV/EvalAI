// Invoking IIFE for challenge page
(function() {

    'use strict';
    angular
        .module('evalai')
        .controller('ChallengeCtrl', ChallengeCtrl);

    ChallengeCtrl.$inject = ['utilities', 'loaderService', '$scope', '$state', '$http', '$stateParams', '$rootScope', '$interval', '$mdDialog', 'moment', '$location', '$anchorScroll', '$timeout'];

    function ChallengeCtrl(utilities, loaderService, $scope, $state, $http, $stateParams, $rootScope, $interval, $mdDialog, moment, $location, $anchorScroll, $timeout) {
        var vm = this;
        vm.areSubmissionsFailing = false;
        vm.getAllEntriesTestOption = "Include private submissions";
        vm.showPrivateIds = [];
        vm.showLeaderboardToggle = true;
        vm.challengeId = $stateParams.challengeId;
        vm.phaseId = null;
        vm.phaseSplitId = $stateParams.phaseSplitId;
        vm.input_file = null;
        vm.fileUrl = "";
        vm.methodName = "";
        vm.methodDesc = "";
        vm.projectUrl = "";
        vm.publicationUrl = "";
        vm.isPublicSubmission = null;
        vm.isMultiMetricLeaderboardEnabled = {};
        vm.wrnMsg = {};
        vm.page = {};
        vm.isParticipated = false;
        vm.isActive = false;
        vm.phases = {};
        vm.phaseSplits = {};
        vm.orderLeaderboardBy = decodeURIComponent($stateParams.metric);
        vm.phaseSplitLeaderboardSchema = {};
        vm.submissionMetaAttributes = []; // Stores the attributes format and phase ID for all the phases of a challenge.
        vm.metaAttributesforCurrentSubmission = null; // Stores the attributes while making a submission for a selected phase.
        vm.selectedPhaseSplit = {};
        vm.phaseRemainingSubmissions = {};
        vm.phaseRemainingSubmissionsFlags = {};
        vm.phaseRemainingSubmissionsCountdown = {};
        vm.isValid = {};
        vm.submissionVisibility = {};
        vm.baselineStatus = {};
        vm.verifiedStatus = {};
        vm.showUpdate = false;
        vm.showLeaderboardUpdate = false;
        vm.poller = null;
        vm.isChallengeHost = false;
        vm.isDockerBased = false;
        vm.stopLeaderboard = function() {};
        vm.stopFetchingSubmissions = function() {};
        vm.currentDate = null;
        vm.isPublished = false;
        vm.approved_by_admin = false;
        vm.sortColumn = 'rank';
        vm.reverseSort = false;
        vm.columnIndexSort = 0;
        vm.disableSubmit = true;
        // save initial ranking
        vm.initial_ranking = {};
        // loader for existing teams
        vm.isExistLoader = false;
        vm.loaderTitle = '';
        vm.loaderContainer = angular.element('.exist-team-card');
        vm.termsAndConditions = false;
        vm.team = {};
        vm.isSubmissionUsingUrl = null;
        vm.isSubmissionUsingCli = null;
        vm.isSubmissionUsingFile = null;
        vm.isRemoteChallenge = false;
        vm.allowedSubmissionFileTypes = [];
        vm.currentPhaseAllowedSubmissionFileTypes = '';
        vm.defaultSubmissionMetaAttributes = [];
        vm.currentSubmissionMetaData = null;
        vm.currentPhaseMetaAttributesVisibility = {};
        vm.phaseLeaderboardPublic = [];
        vm.currentPhaseLeaderboardPublic = false;

        vm.filter_all_submission_by_team_name = '';
        vm.filter_my_submission_by_team_name = '';
        // show loader
        vm.startLoader = loaderService.startLoader;
        // stop loader
        vm.stopLoader = loaderService.stopLoader;

        var userKey = utilities.getData('userKey');
        vm.authToken = userKey;

        vm.refreshJWT = utilities.getData('refreshJWT');

        vm.subErrors = {};
        vm.currentHighlightedLeaderboardEntry = null;

        vm.isChallengeLeaderboardPrivate = false;
        vm.previousPublicSubmissionId = null;

        vm.workerLogs = [];

        utilities.showLoader();

        // scroll to the selected entry after page has been rendered
        vm.scrollToEntryAfterLeaderboardLoads = function () {
            // get unique rank number from the url & if exists hightlight the entry
            $timeout(function() {
                var elementId = $location.absUrl().split('?')[0].split('#')[1];
                if (elementId) {
                    $anchorScroll.yOffset = 90;
                    $anchorScroll(elementId);
                    $scope.isHighlight = elementId.split("leaderboardrank-")[1];
                }
            }, 500);
        };

        // Function to fetch and set refreshJWT 
        vm.fetchRefreshJWTToken = function () {
            if (userKey) {
                var parameters = {};
                parameters.url = 'accounts/user/get_auth_token';
                parameters.method = 'GET';
                parameters.token = userKey;
                parameters.callback = {
                    onSuccess: function (response) {
                        if (response.status == 200) {
                            utilities.storeData('refreshJWT', response.data.token);
                            vm.refreshJWT = utilities.getData('refreshJWT');
                        } else {
                            alert("Could not fetch Auth Token");
                        }
                    },
                    onError: function (response) {
                        if (response.status == 400) {
                            vm.isFormError = true;
                            var non_field_errors;
                            try {
                                non_field_errors = typeof (response.data.non_field_errors) !== 'undefined' ? true : false;
                                if (non_field_errors) {
                                    vm.FormError = response.data.non_field_errors[0];
                                }
                            } catch (error) {
                                $rootScope.notify("error", error);
                            }
                        }
                    }
                };
                utilities.sendRequest(parameters, "header");
            }
        };

        // check if the user is already logged in and jwt token is not set
        if (typeof vm.refreshJWT != "string") {
            vm.fetchRefreshJWTToken();
        }

        // API call to manage the worker from UI.
        // Response data will be like: {action: "Success" or "Failure", error: <String to include only if action is Failure.>}
        vm.manageWorker = function(action){
            parameters.url = 'challenges/' + vm.challengeId + '/manage_worker/' + action +'/';
            parameters.method = 'PUT';
            parameters.data = {};
            parameters.callback = {
                onSuccess: function(response) {
                    var details = response.data;
                    if (details.action == "Success"){
                        $rootScope.notify("success", "Worker(s) " + action + "ed succesfully.");
                    }
                    else {
                        $rootScope.notify("error", details.error);
                    }
                },
                onError: function(response) {
                    var error = response.data.error;
                    if (error == undefined){
                        $rootScope.notify("error", "There was an error.");
                    }
                    else {
                        $rootScope.notify("error", "There was an error: " + error);
                    }
                }
            };
            utilities.sendRequest(parameters);
        };

        // Get the logs from worker if submissions are failing.
        vm.startLoadingLogs = function() {
            vm.logs_poller = $interval(function(){
                parameters.url = 'challenges/' + vm.challengeId + '/get_worker_logs/';
                parameters.method = 'GET';
                parameters.data = {};
                parameters.callback = {
                    onSuccess: function(response) {
                        var details = response.data;
                        vm.workerLogs = [];
                        for (var i = 0; i<details.logs.length; i++){
                            vm.workerLogs.push(details.logs[i]);
                        }
                    },
                    onError: function(response) {
                        var error = response.data.error;
                        vm.workerLogs.push(error);
                    }
                };
                utilities.sendRequest(parameters);
            }, 5000);
        };

        vm.stopLoadingLogs = function(){
            $interval.cancel(vm.logs_poller);
        };

         // highlight the specific entry of the leaderboard
        vm.highlightSpecificLeaderboardEntry = function (key) {
            key = '#' + key;
            // Remove highlight from previous clicked entry
            if (vm.currentHighlightedLeaderboardEntry != null) {
                let prevEntry = angular.element(vm.currentHighlightedLeaderboardEntry)[0];
                prevEntry.setAttribute("class", "");
            }
            let entry = angular.element(key)[0];
            entry.setAttribute("class", "highlightLeaderboard");
            vm.currentHighlightedLeaderboardEntry = key;
            $scope.isHighlight = false;
        };

        // get names of the team that has participated in the current challenge
        vm.getTeamName = function(challengeId) {
            parameters.url = 'challenges/' + challengeId + '/participant_team/team_detail';
            parameters.method = 'GET';
            parameters.data={};
            parameters.callback = {
                onSuccess: function(response) {
                     var details = response.data;
                    vm.participated_team_name = details["team_name"];
                },
            };
            utilities.sendRequest(parameters);
        };

            vm.displayDockerSubmissionInstructions = function (isDockerBased, isParticipated) {
            // get remaining submission for docker based challenge
            if (isDockerBased && isParticipated == true) {
                parameters.url = 'jobs/' + vm.challengeId + '/remaining_submissions/';
                parameters.method = 'GET';
                parameters.data = {};
                parameters.callback = {
                    onSuccess: function (response) {
                        vm.phaseRemainingSubmissions = response.data;
                        var details = vm.phaseRemainingSubmissions.phases;
                        for (var i = 0; i < details.length; i++) {
                            if (details[i].limits.submission_limit_exceeded === true) {
                                vm.phaseRemainingSubmissionsFlags[details[i].id] = "maxExceeded";
                            } else if (details[i].limits.remaining_submissions_today_count > 0) {
                                vm.phaseRemainingSubmissionsFlags[details[i].id] = "showSubmissionNumbers";
                            } else {
                                vm.eachPhase = details[i];
                                vm.phaseRemainingSubmissionsFlags[details[i].id] = "showClock";
                                vm.countDownTimer = function () {
                                    vm.remainingTime = vm.eachPhase.limits.remaining_time;
                                    vm.days = Math.floor(vm.remainingTime / 24 / 60 / 60);
                                    vm.hoursLeft = Math.floor((vm.remainingTime) - (vm.days * 86400));
                                    vm.hours = Math.floor(vm.hoursLeft / 3600);
                                    vm.minutesLeft = Math.floor((vm.hoursLeft) - (vm.hours * 3600));
                                    vm.minutes = Math.floor(vm.minutesLeft / 60);
                                    vm.remainingSeconds = Math.floor(vm.remainingTime % 60);
                                    if (vm.remainingSeconds < 10) {
                                        vm.remainingSeconds = "0" + vm.remainingSeconds;
                                    }
                                    vm.phaseRemainingSubmissionsCountdown[details[i].id] = {
                                        "days": vm.days,
                                        "hours": vm.hours,
                                        "minutes": vm.minutes,
                                        "seconds": vm.remainingSeconds
                                    };
                                    if (vm.remainingTime === 0) {
                                        vm.phaseRemainingSubmissionsFlags[details[i].id] = "showSubmissionNumbers";
                                    } else {
                                        vm.remainingSeconds--;
                                    }
                                };
                                setInterval(function () {
                                    $rootScope.$apply(vm.countDownTimer);
                                }, 1000);
                                vm.countDownTimer();
                            }
                        }
                        utilities.hideLoader();
                    },
                    onError: function (response) {
                        var error = response.data;
                        utilities.storeData('emailError', error.detail);
                        $state.go('web.permission-denied');
                    }
                };
                utilities.sendRequest(parameters);
            }
        };

        // get details of the particular challenge
        var parameters = {};
        parameters.token = null;
        if (userKey) {
            parameters.token = userKey;
        }
        parameters.method = 'GET';
        parameters.url = 'challenges/challenge/' + vm.challengeId + '/';
        parameters.data = {};
        parameters.callback = {
            onSuccess: function(response) {
                var details = response.data;
                vm.page = details;
                vm.isActive = details.is_active;
                vm.isPublished = vm.page.published;
                vm.isForumEnabled = details.enable_forum;
                vm.forumURL = details.forum_url;
                vm.cliVersion = details.cli_version;
                vm.isRegistrationOpen = details.is_registration_open;
                vm.approved_by_admin = details.approved_by_admin;
                vm.isRemoteChallenge = details.remote_evaluation;
                vm.getTeamName(vm.challengeId);

                if (vm.page.image === null) {
                    vm.page.image = "dist/images/logo.png";

                }

                if (userKey) {

                    // get details of challenges corresponding to participant teams of that user
                    parameters.url = 'participants/participant_teams/challenges/' + vm.challengeId + '/user';
                    parameters.method = 'GET';
                    parameters.data = {};
                    parameters.callback = {
                        onSuccess: function(response) {
                            var details = response.data;
                            vm.currentDate = details.datetime_now;
                            for (var i in details.challenge_participant_team_list) {
                                if (details.challenge_participant_team_list[i].challenge !== null && details.challenge_participant_team_list[i].challenge.id == vm.challengeId) {
                                    vm.isParticipated = true;
                                    break;
                                }
                            }

                            if (details.is_challenge_host) {
                                vm.isChallengeHost = true;
                            }

                            if (!vm.isParticipated) {

                                vm.team = {};
                                vm.teamId = null;
                                vm.existTeam = {};
                                vm.currentPage = '';
                                vm.isNext = '';
                                vm.isPrev = '';
                                vm.team.error = false;

                                parameters.url = 'participants/participant_team';
                                parameters.method = 'GET';
                                parameters.callback = {
                                    onSuccess: function(response) {
                                        var status = response.status;
                                        var details = response.data;
                                        if (status == 200) {
                                            vm.existTeam = details;

                                            if (vm.existTeam.count === 0) {
                                                vm.showPagination = false;
                                                vm.paginationMsg = "No team exists for now. Start by creating a new team!";
                                            } else {
                                                vm.showPagination = true;
                                                vm.paginationMsg = "";
                                            }

                                            // clear error msg from storage
                                            utilities.deleteData('emailError');

                                            // condition for pagination
                                            if (vm.existTeam.next === null) {
                                                vm.isNext = 'disabled';
                                            } else {
                                                vm.isNext = '';
                                            }

                                            if (vm.existTeam.previous === null) {
                                                vm.isPrev = 'disabled';
                                            } else {
                                                vm.isPrev = '';
                                            }
                                            if (vm.existTeam.next !== null) {
                                                vm.currentPage = vm.existTeam.next.split('page=')[1] - 1;
                                            } else {
                                                vm.currentPage = 1;
                                            }


                                            // select team from existing list
                                            vm.selectExistTeam = function() {

                                                // loader for existing teams
                                                vm.isExistLoader = true;
                                                vm.loaderTitle = '';
                                                vm.loaderContainer = angular.element('.exist-team-card');

                                                // show loader
                                                vm.startLoader("Loading Teams");
                                                // loader end

                                                parameters.url = 'challenges/challenge/' + vm.challengeId + '/participant_team/' + vm.teamId;
                                                parameters.method = 'POST';
                                                parameters.callback = {
                                                    onSuccess: function() {
                                                        vm.isParticipated = true;
                                                        $state.go('web.challenge-main.challenge-page.submission');
                                                        vm.displayDockerSubmissionInstructions(vm.page.is_docker_based, vm.isParticipated);
                                                        vm.getTeamName(vm.challengeId);
                                                        vm.stopLoader();
                                                    },
                                                    onError: function(response) {
                                                        if (response.status == 404) {
                                                            var error = "Please select a team first!";
                                                        } else {
                                                            error = response.data["error"];
                                                        }
                                                        $rootScope.notify("error", error);
                                                        vm.stopLoader();
                                                    }
                                                };
                                                utilities.sendRequest(parameters);
                                            };

                                            // to load data with pagination
                                            vm.load = function(url) {
                                                // loader for existing teams
                                                vm.isExistLoader = true;
                                                vm.loaderTitle = '';
                                                vm.loaderContainer = angular.element('.exist-team-card');


                                                vm.startLoader("Loading Teams");
                                                if (url !== null) {

                                                    //store the header data in a variable
                                                    var headers = {
                                                        'Authorization': "Token " + userKey
                                                    };

                                                    //Add headers with in your request
                                                    $http.get(url, { headers: headers }).then(function(response) {
                                                        // reinitialized data
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
                                                }
                                            };

                                        }
                                        utilities.hideLoader();
                                    },
                                    onError: function(response) {
                                        var error = response.data;
                                        utilities.storeData('emailError', error.detail);
                                        $state.go('web.permission-denied');
                                        utilities.hideLoader();
                                    }
                                };

                                utilities.sendRequest(parameters);

                            }
                            vm.displayDockerSubmissionInstructions(vm.page.is_docker_based, vm.isParticipated);
                            utilities.hideLoader();
                        },
                        onError: function() {
                            utilities.hideLoader();
                        }
                    };
                    utilities.sendRequest(parameters);
                }

                utilities.hideLoader();

            },
            onError: function(response) {
                var error = response.data;
                $rootScope.notify("error", error.error);
                $state.go('web.dashboard');
                utilities.hideLoader();
            }
        };

        utilities.sendRequest(parameters);

        vm.toggleParticipation = function (ev, isRegistrationOpen) {
            // ev.stopPropagation();
            var participationState;
            var participationModalText;
            if (isRegistrationOpen) {
                participationState = 'closed';
                participationModalText = 'Close participation in the challenge?';
            } else {
                participationState = 'opened';
                participationModalText = 'Open participation in the challenge?';
            }
            var confirm = $mdDialog.confirm()
                          .title(participationModalText)
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
                        $rootScope.notify('success', 'Participation is ' + participationState + ' successfully');
                    },
                    onError: function(response) {
                        var details = response.data;
                        $rootScope.notify('error', details.error);
                    }
                };
                utilities.sendRequest(parameters);
            }, function() {});
        };

        vm.makeSubmission = function() {
            if (vm.isParticipated) {
                var fileVal = angular.element(".file-path").val();
                if ((fileVal === null || fileVal === "") && (vm.fileUrl === null || vm.fileUrl === "")) {
                    vm.subErrors.msg = "Please upload file or enter submission URL!";
                } else {
                    if (vm.isCurrentSubmissionMetaAttributeValid() !== true) {
                        vm.subErrors.msg = "Please provide input for meta attributes!";
                        return false;
                    }
                    vm.isExistLoader = true;
                    vm.loaderTitle = '';
                    vm.loaderContainer = angular.element('.exist-team-card');


                    vm.startLoader("Making Submission");
                    if (vm.input_file) {
                        // vm.upload(vm.input_file);
                    }
                    parameters.url = 'jobs/challenge/' + vm.challengeId + '/challenge_phase/' + vm.phaseId + '/submission/';
                    parameters.method = 'POST';
                    var formData = new FormData();
                    if (vm.isSubmissionUsingUrl) {
                        var urlRegex = /(ftp|http|https):\/\/(\w+:{0,1}\w*@)?(\S+)(:[0-9]+)?(\/|\/([\w#!:.?+=&%@!\-/]))?/;
                        var validExtensions = vm.currentPhaseAllowedSubmissionFileTypes;
                        var isUrlValid = urlRegex.test(vm.fileUrl);
                        var extension = vm.fileUrl.split(".").pop();
                        if (isUrlValid && validExtensions.includes(extension)) {
                            formData.append("file_url", vm.fileUrl);
                        } else {
                            vm.stopLoader();
                            vm.subErrors.msg = "Please enter a valid URL which ends in " + validExtensions + " file extension!";
                            return false;
                        }
                    } else {
                        formData.append("input_file", vm.input_file);
                    }
                    formData.append("status", "submitting");
                    formData.append("method_name", vm.methodName);
                    formData.append("method_description", vm.methodDesc);
                    formData.append("project_url", vm.projectUrl);
                    formData.append("publication_url", vm.publicationUrl);
                    formData.append("submission_metadata", JSON.stringify(vm.metaAttributesforCurrentSubmission));
                    if (vm.isPublicSubmission !== null) {
                        formData.append("is_public", vm.isPublicSubmission);
                    }

                    parameters.data = formData;

                    parameters.token = userKey;
                    parameters.callback = {
                        onSuccess: function() {
                            // vm.input_file.name = '';

                            angular.forEach(
                                angular.element("input[type='file']"),
                                function(inputElem) {
                                    angular.element(inputElem).val(null);
                                }
                            );

                            angular.element(".file-path").val(null);


                            // Reset the value of fields related to a submission
                            vm.phaseId = null;
                            vm.fileUrl = "";
                            vm.methodName = "";
                            vm.methodDesc = "";
                            vm.projectUrl = "";
                            vm.publicationUrl = "";
                            vm.isPublicSubmission = null;
                            $rootScope.notify("success", "Your submission has been recorded succesfully!");
                            vm.disableSubmit = true;
                            vm.showSubmissionNumbers = false;
                            vm.metaAttributesforCurrentSubmission = null;
                            vm.stopLoader();
                        },
                        onError: function(response) {
                            var status = response.status;
                            var error = response.data;

                            vm.phaseId = null;
                            vm.fileUrl = null;
                            vm.methodName = null;
                            vm.methodDesc = null;
                            vm.projectUrl = null;
                            vm.publicationUrl = null;
                            vm.isPublicSubmission = null;
                            if (status == 404) {
                                vm.subErrors.msg = "Please select phase!";
                            } else {
                                if (error.error){
                                    vm.subErrors.msg = error.error;
                                } else {
                                    vm.subErrors.msg = error.input_file[0];
                                }
                            }
                            vm.stopLoader();
                        }
                    };
                    utilities.sendRequest(parameters, 'header', 'upload');
                }
            }
        };

        // get details of the particular challenge phase
        parameters.url = 'challenges/challenge/' + vm.challengeId + '/challenge_phase';
        parameters.method = 'GET';
        parameters.data = {};
        parameters.callback = {
            onSuccess: function(response) {
                var details = response.data;
                vm.phases = details;
                var timezone = moment.tz.guess();
                for (var i=0; i<details.count; i++) {
                    if (details.results[i].is_public == false) {
                        vm.phases.results[i].showPrivate = true;
                    }
                }
                for (var j=0; j<vm.phases.results.length; j++){
                    var offset = new Date(vm.phases.results[j].start_date).getTimezoneOffset();
                    vm.phases.results[j].start_zone = moment.tz.zone(timezone).abbr(offset);
                    offset = new Date(vm.phases.results[j].end_date).getTimezoneOffset();
                    vm.phases.results[j].end_zone = moment.tz.zone(timezone).abbr(offset);
                }

                for(var k=0; k<details.count; k++){
                    if (details.results[k].submission_meta_attributes != undefined || details.results[k].submission_meta_attributes != null){
                        var attributes = details.results[k].submission_meta_attributes;
                        attributes.forEach(function(attribute){
                            if (attribute["type"] == "checkbox") {
                                attribute["values"] = [];
                            }
                            else {
                                attribute["value"] = null;
                            }
                        });
                        data = {"phaseId":details.results[k].id, "attributes": attributes};
                        vm.submissionMetaAttributes.push(data);
                    }
                    else {
                        var data = {"phaseId":details.results[k].id, "attributes": null};
                        vm.submissionMetaAttributes.push(data);
                    }
                    if (details.results[k].allowed_submission_file_types != undefined || details.results[k].allowed_submission_file_types != null) {
                        vm.allowedSubmissionFileTypes.push({
                            "phaseId": details.results[k].id,
                            "allowedSubmissionFileTypes": details.results[k].allowed_submission_file_types
                        });
                    } else {
                        // Handle case for missing values
                        vm.allowedSubmissionFileTypes.push({
                            "phaseId": details.results[k].id,
                            "allowedSubmissionFileTypes": ".json, .zip, .txt, .tsv, .gz, .csv, .h5, .npy"
                        });
                    }
                    if (details.results[k].default_submission_meta_attributes != undefined && details.results[k].default_submission_meta_attributes != null) {
                        var meta_attributes = details.results[k].default_submission_meta_attributes;
                        var defaultMetaAttributes = vm.getDefaultMetaAttributesDict(meta_attributes);
                        vm.defaultSubmissionMetaAttributes.push({
                            "phaseId": details.results[k].id,
                            "defaultAttributes": defaultMetaAttributes
                        });
                    } else {
                        vm.defaultSubmissionMetaAttributes.push({
                            "phaseId":details.results[k].id,
                            "defaultAttributes": {}
                        });
                    }
                    vm.phaseLeaderboardPublic.push({
                        "phaseId": details.results[k].id,
                        "leaderboardPublic": details.results[k].leaderboard_public
                    });
                }
                utilities.hideLoader();
            },
            onError: function(response) {
                var error = response.data;
                utilities.storeData('emailError', error.detail);
                $state.go('web.permission-denied');
                utilities.hideLoader();
            }
        };

        utilities.sendRequest(parameters);

        vm.loadPhaseAttributes = function(phaseId){ // Loads attributes of a phase into vm.submissionMetaAttributes
            vm.metaAttributesforCurrentSubmission = vm.submissionMetaAttributes.find(function(element){
                return element["phaseId"] == phaseId;
            }).attributes;
            vm.currentPhaseAllowedSubmissionFileTypes = vm.allowedSubmissionFileTypes.find(function(element) {
                return element["phaseId"] == phaseId;
            }).allowedSubmissionFileTypes;
            // load default meta attributes visibility for current phase
            vm.currentPhaseMetaAttributesVisibility = vm.defaultSubmissionMetaAttributes.find(function(element) {
                return element["phaseId"] == phaseId;
            }).defaultAttributes;
            vm.currentPhaseLeaderboardPublic = vm.phaseLeaderboardPublic.find(function(element) {
                return element["phaseId"] == phaseId;
            }).leaderboardPublic;
            vm.subErrors.msg = "";
        };

        vm.getDefaultMetaAttributesDict = function(defaultMetaAttributes) {
            var defaultMetaAttributesDict = {};
            if (defaultMetaAttributes != undefined && defaultMetaAttributes != null) {
                defaultMetaAttributes.forEach(function(attribute) {
                    var attributeName = attribute["name"];
                    var is_visible = attribute["is_visible"];
                    defaultMetaAttributesDict[attributeName] = is_visible;
                });
            }
            return defaultMetaAttributesDict;
        };

        vm.clearMetaAttributeValues = function(){
            if (vm.metaAttributesforCurrentSubmission != null){
                vm.metaAttributesforCurrentSubmission.forEach(function(attribute){
                    if (attribute.type == 'checkbox'){
                        attribute.values = [];
                    }
                    else {
                        attribute.value = null;
                    }
                });
            }
        };

        vm.isCurrentSubmissionMetaAttributeValid = function() {
            var isMetaAttributeValid = true;
            if (vm.metaAttributesforCurrentSubmission !== null) {
                vm.metaAttributesforCurrentSubmission.forEach(function(attribute) {
                    if (attribute.required == true) {
                        if (attribute.type == "checkbox") {
                            if (attribute.values.length === 0) {
                                isMetaAttributeValid = false;
                            }
                        } else {
                            if (attribute.value === null || attribute.value === undefined) {
                                isMetaAttributeValid = false;
                            }
                        }
                    }
                });
            }
            return isMetaAttributeValid;
        };

        vm.toggleSelection = function toggleSelection(attribute, value){ // Make sure this modifies the reference object.
                var idx = attribute.values.indexOf(value);
                if (idx > -1) {
                  attribute.values.splice(idx, 1);
                }
                else {
                  attribute.values.push(value);
                }
            };

        var challengePhaseVisibility = {
            owner_and_host: 1,
            host: 2,
            public: 3,
        };

        // get details of the particular challenge phase split
        parameters.url = 'challenges/' + vm.challengeId + '/challenge_phase_split';
        parameters.method = 'GET';
        parameters.data = {};
        parameters.callback = {
            onSuccess: function(response) {
                var details = response.data;
                vm.phaseSplits = details;
                if (details.length == 0) {
                    vm.isChallengeLeaderboardPrivate = true; 
                }
                for(var i=0; i<details.length; i++) {
                    if (details[i].visibility !== challengePhaseVisibility.public) {
                        vm.phaseSplits[i].showPrivate = true;
                        vm.showPrivateIds.push(vm.phaseSplits[i].id);
                    }
                    vm.isMultiMetricLeaderboardEnabled[vm.phaseSplits[i].id] = vm.phaseSplits[i].is_multi_metric_leaderboard;
                    vm.phaseSplitLeaderboardSchema[vm.phaseSplits[i].id] = vm.phaseSplits[i].leaderboard_schema;
                }
                utilities.hideLoader();
            },
            onError: function(response) {
                var error = response.data;
                utilities.storeData('emailError', error.detail);
                $state.go('web.permission-denied');
                utilities.hideLoader();
            }
        };

        utilities.sendRequest(parameters);

        // define a custom sorting function
        vm.lastKey = null;
        vm.sortFunction = function(key) {
            // check which column is selected
            // so that the values can be parsed properly
            if (vm.sortColumn === 'date') {
                return Date.parse(key.submission__submitted_at_formatted);
            }
            else if (vm.sortColumn === 'rank') {
                return vm.initial_ranking[key.id];
            }
            else if (vm.sortColumn === 'number') {
                return parseFloat(key.result[vm.columnIndexSort]);
            }
            else if (vm.sortColumn === 'string'){
                // sort teams alphabetically
                return key.submission__participant_team__team_name;
            }
            else if (vm.sortColumn == 'exec'){
                return key.submission__execution_time;
            }
            return 0;
        };

        vm.sortLeaderboard = function(scope, column, index) {
            if (index == null || index == undefined) {
                scope.reverseSort = scope.sortColumn != column ? false : !scope.reverseSort;
            } else {
                scope.reverseSort = scope.sortColumn == column && scope.columnIndexSort == index ? !scope.reverseSort : false;
                scope.columnIndexSort = index;
            }
            scope.sortColumn = column;
        };

        vm.isMetricOrderedAscending = function(metric) {
            let schema = vm.leaderboard[0].leaderboard__schema;
            let metadata = schema.metadata;
            if (metadata != null && metadata != undefined) {
                // By default all metrics are considered higher is better
                if (metadata[metric] == undefined) {
                    return false;
                }
                return metadata[metric].sort_ascending;
            }
            return false;
        };

        vm.getLabelDescription = function(metric) {
            let schema = vm.leaderboard[0].leaderboard__schema;
            let metadata = schema.metadata;
            if (metadata != null && metadata != undefined) {
                // By default all metrics are considered higher is better
                if (metadata[metric] == undefined || metadata[metric].description == undefined) {
                    return "";
                }
                return metadata[metric].description;
            }
            return "";
        };

        // my submissions
        vm.isResult = false;

        vm.startLeaderboard = function() {
            vm.stopLeaderboard();
            vm.poller = $interval(function() {
                parameters.url = "jobs/" + "challenge_phase_split/" + vm.phaseSplitId + "/leaderboard/?page_size=1000&order_by=" + vm.orderLeaderboardBy;
                parameters.method = 'GET';
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
            }, 10000);
        };

        vm.getLeaderboard = function(phaseSplitId) {
            vm.stopLeaderboard = function() {
                $interval.cancel(vm.poller);
            };
            vm.stopLeaderboard();

            vm.isResult = true;
            vm.phaseSplitId = phaseSplitId;
            // loader for existing teams
            vm.isExistLoader = true;
            vm.loaderTitle = '';
            vm.loaderContainer = angular.element('.exist-team-card');

            vm.startLoader("Loading Leaderboard Items");

            // get the selected phase split object
            parameters.url = "challenges/challenge/create/challenge_phase_split/" + vm.phaseSplitId + "/";
            parameters.method = "GET";
            parameters.data = {};
            parameters.callback = {
                onSuccess: function (response) {
                    vm.selectedPhaseSplit = response.data;
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

            // Show leaderboard
            vm.leaderboard = {};
            parameters.url = "jobs/" + "challenge_phase_split/" + vm.phaseSplitId + "/leaderboard/?page_size=1000&order_by=" + vm.orderLeaderboardBy;
            parameters.method = 'GET';
            parameters.callback = {
                onSuccess: function(response) {
                    var details = response.data;
                    vm.leaderboard = details.results;
                    for (var j=0; j<vm.showPrivateIds.length; j++) {
                        if (vm.showPrivateIds[j] == vm.phaseSplitId) {
                            vm.showLeaderboardToggle = false;
                            break;
                        }
                    }
                    for (var i=0; i<vm.leaderboard.length; i++) {
                        if (vm.leaderboard[i].submission__submission_metadata == null){
                            vm.showSubmissionMetaAttributesOnLeaderboard = false;
                        }
                        else {
                            vm.showSubmissionMetaAttributesOnLeaderboard = true;
                        }

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
                    vm.phaseName = vm.phaseSplitId;
                    vm.startLeaderboard();
                    vm.stopLoader();
                    vm.scrollToEntryAfterLeaderboardLoads();
                },
                onError: function(response) {
                    var error = response.data;
                    vm.leaderboard.error = error;
                    vm.stopLoader();
                }
            };

            utilities.sendRequest(parameters);
        };

        if (vm.phaseSplitId) {
            vm.getLeaderboard(vm.phaseSplitId);
        }

        
        vm.showMetaAttributesDialog = function(ev, attributes){
            if (attributes != false){
                vm.metaAttributesData = [];
                attributes.forEach(function(attribute){
                    if (attribute.type != "checkbox") {
                        vm.metaAttributesData.push({"name": attribute.name, "value": attribute.value});
                    }
                    else {
                        vm.metaAttributesData.push({"name": attribute.name, "values": attribute.values});
                    }
                });

                $mdDialog.show({
                    scope: $scope,
                    preserveScope: true,
                    targetEvent: ev,
                    templateUrl: 'src/views/web/challenge/submission-meta-attributes-dialog.html',
                    clickOutsideToClose: true
                });
            }
            else {
                $mdDialog.hide();
            }
        };

        vm.getResults = function(phaseId) {
            // long polling (5s) for leaderboard
            vm.start = function() {
                vm.stopFetchingSubmissions();
                vm.poller = $interval(function() {
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
                                vm.verifiedStatus[details.results[i].id] = details.results[i].is_verified_by_host;
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
                }, 10000);
            };

            vm.stopFetchingSubmissions = function() {
                $interval.cancel(vm.poller);
            };
            vm.stopFetchingSubmissions();
            vm.isResult = true;
            if (phaseId !== undefined) {
                vm.phaseId = phaseId;
            }

            var all_phases = vm.phases.results;
            for (var i = 0; i < vm.phases.results.length; i++) {
                if (all_phases[i].id == phaseId) {
                    vm.currentPhaseLeaderboardPublic = all_phases[i].leaderboard_public;
                    vm.isCurrentPhaseRestrictedToSelectOneSubmission = all_phases[i].is_restricted_to_select_one_submission;

                    var attributes = all_phases[i].default_submission_meta_attributes;
                    var defaultMetaAttributes = vm.getDefaultMetaAttributesDict(attributes);
                    vm.currentPhaseMetaAttributesVisibility = defaultMetaAttributes;
                    break;
                }
            }

            parameters.url = "analytics/challenge/" + vm.challengeId + "/challenge_phase/" + vm.phaseId + "/count";
            parameters.method = 'GET';
            parameters.data = {};
            parameters.callback = {
                onSuccess: function(response) {
                    var details = response.data;
                    vm.submissionCount = details.participant_team_submission_count;
                },
                onError: function(response) {
                    var error = response.data;
                    $rootScope.notify("error", error);
                }
            };
            utilities.sendRequest(parameters);

            // loader for existing teams
            vm.isExistLoader = true;
            vm.loaderTitle = '';
            vm.loaderContainer = angular.element('.exist-team-card');

            vm.startLoader("Loading Submissions");

            // get submissions of a particular challenge phase
            vm.isNext = '';
            vm.isPrev = '';
            vm.currentPage = '';
            vm.showPagination = false;

            if (vm.filter_my_submission_by_team_name === '') {
                parameters.url = "jobs/challenge/" + vm.challengeId + "/challenge_phase/" +
                vm.phaseId + "/submission/";
            } else {
                parameters.url = "jobs/challenge/" + vm.challengeId + "/challenge_phase/" +
                vm.phaseId + "/submission?participant_team__team_name=" + vm.filter_my_submission_by_team_name;
            }
            parameters.method = 'GET';
            parameters.data = {};
            parameters.callback = {
                onSuccess: function(response) {
                    var details = response.data;

                    for (var i = 0; i < details.results.length; i++) {
                        vm.submissionVisibility[details.results[i].id] = details.results[i].is_public;
                        vm.baselineStatus[details.results[i].id] = details.results[i].is_baseline;
                        vm.verifiedStatus[details.results[i].id] = details.results[i].is_verified_by_host;
                        // Set previous public submission id for phases with one public submission restriction
                        if (details.results[i].is_public) {
                            vm.previousPublicSubmissionId = details.results[i].id;
                        }
                    }

                    vm.submissionResult = details;

                    vm.start();

                    if (vm.submissionResult.count === 0) {
                        vm.showPagination = false;
                        vm.paginationMsg = "No results found";
                    } else {

                        vm.showPagination = true;
                        vm.paginationMsg = "";
                    }

                    if (vm.submissionResult.next === null) {
                        vm.isNext = 'disabled';
                    } else {
                        vm.isNext = '';

                    }
                    if (vm.submissionResult.previous === null) {
                        vm.isPrev = 'disabled';
                    } else {
                        vm.isPrev = '';
                    }
                    if (vm.submissionResult.next !== null) {
                        vm.currentPage = vm.submissionResult.next.split('page=')[1] - 1;
                        vm.currentRefPage = Math.ceil(vm.currentPage);
                    } else {
                        vm.currentPage = 1;
                        vm.currentRefPage = Math.ceil(vm.currentPage);
                    }

                    vm.load = function(url) {
                        // loader for existing teams
                        vm.isExistLoader = true;
                        vm.loaderTitle = '';
                        vm.loaderContainer = angular.element('.exist-team-card');

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
                                    vm.currentPage = vm.submissionResult.count / 150;
                                    vm.currentRefPage = Math.ceil(vm.currentPage);
                                } else {
                                    vm.isNext = '';
                                    vm.currentPage = parseInt(vm.submissionResult.next.split('page=')[1] - 1);
                                    vm.currentRefPage = Math.ceil(vm.currentPage);
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
                    };
                    vm.stopLoader();
                },
                onError: function(response) {
                    var error = response.data;
                    utilities.storeData('emailError', error.detail);
                    $state.go('web.permission-denied');
                    vm.stopLoader();
                }
            };

            utilities.sendRequest(parameters);
        };

        vm.refreshSubmissionData = function() {

            // get submissions of a particular challenge phase

            if (!vm.isResult) {

                vm.isNext = '';
                vm.isPrev = '';
                vm.currentPage = '';
                vm.currentRefPage = '';
                vm.showPagination = false;
            }

            vm.startLoader("Loading Submissions");
            vm.submissionResult = {};

            parameters.url = "jobs/challenge/" + vm.challengeId + "/challenge_phase/" + vm.phaseId + "/submission/?page=" + Math.ceil(vm.currentPage);
            parameters.method = 'GET';
            parameters.data = {};
            parameters.callback = {
                onSuccess: function(response) {
                    var details = response.data;
                    vm.submissionResult = details;

                    if (vm.submissionResult.count === 0) {
                        vm.showPagination = false;
                        vm.paginationMsg = "No results found";
                    } else {

                        vm.showPagination = true;
                        vm.paginationMsg = "";
                    }

                    if (vm.submissionResult.next === null) {
                        vm.isNext = 'disabled';
                    } else {
                        vm.isNext = '';

                    }
                    if (vm.submissionResult.previous === null) {
                        vm.isPrev = 'disabled';
                    } else {
                        vm.isPrev = '';
                    }
                    if (vm.submissionResult.next !== null) {
                        vm.currentPage = vm.submissionResult.next.split('page=')[1] - 1;
                        vm.currentRefPage = Math.ceil(vm.currentPage);
                    } else {
                        vm.currentPage = 1;
                        vm.currentRefPage = Math.ceil(vm.currentPage);
                    }


                    // Set the is_public flag corresponding to each submission
                    for (var i = 0; i < details.results.length; i++) {
                        vm.submissionVisibility[details.results[i].id] = details.results[i].is_public;
                        vm.baselineStatus[details.results[i].id] = details.results[i].is_baseline;
                        vm.verifiedStatus[details.results[i].id] = details.results[i].is_verified_by_host;
                    }

                    vm.submissionResult = details;
                    vm.showUpdate = false;
                    vm.stopLoader();
                },
                onError: function() {
                    vm.stopLoader();
                }
            };

            utilities.sendRequest(parameters);
        };

        vm.reRunSubmission = function(submissionObject) {
            submissionObject.classList = ['spin', 'progress-indicator'];
            parameters.url = 'jobs/submissions/' + submissionObject.id + '/re-run-by-host/';
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

        vm.refreshLeaderboard = function() {
            vm.startLoader("Loading Leaderboard Items");
            vm.leaderboard = {};
            parameters.url = "jobs/" + "challenge_phase_split/" + vm.phaseSplitId + "/leaderboard/?page_size=1000&order_by=" + vm.orderLeaderboardBy;
            parameters.method = 'GET';
            parameters.callback = {
                onSuccess: function(response) {
                    var details = response.data;
                    vm.leaderboard = details.results;
                    vm.startLeaderboard();
                    vm.stopLoader();
                },
                onError: function(response) {
                    var error = response.data;
                    vm.leaderboard.error = error;
                    vm.stopLoader();
                }
            };

            utilities.sendRequest(parameters);
        };

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

        // function for getting all submissions on leaderboard public/private
        vm.getAllEntriesOnPublicLeaderboard = function(phaseSplitId) {
            vm.stopLeaderboard = function() {
                $interval.cancel(vm.poller);
            };
            vm.stopLeaderboard();

            vm.isResult = true;
            vm.phaseSplitId = phaseSplitId;
            // loader for exisiting teams
            vm.isExistLoader = true;
            vm.loaderTitle = '';
            vm.loaderContainer = angular.element('.exist-team-card');

            vm.startLoader("Loading Leaderboard Items");

            // Show leaderboard
            vm.leaderboard = {};
            parameters.url = "jobs/" + "phase_split/" + vm.phaseSplitId + "/public_leaderboard_all_entries/?page_size=1000&order_by=" + vm.orderLeaderboardBy;
            parameters.method = 'GET';
            parameters.callback = {
                onSuccess: function(response) {
                    var details = response.data;
                    vm.leaderboard = details.results;

                    // setting last_submission time
                    for (var i = 0; i < vm.leaderboard.length; i++) {
                        vm.leaderboard[i]['submission__submitted_at_formatted'] = vm.leaderboard[i]['submission__submitted_at'];
                        vm.initial_ranking[vm.leaderboard[i].id] = i + 1;
                        var dateTimeNow = moment(new Date());
                        var submissionTime = moment(vm.leaderboard[i].submission__submitted_at);
                        var duration = moment.duration(dateTimeNow.diff(submissionTime));
                        if (duration._data.years != 0) {
                            var years = duration.asYears();
                            vm.leaderboard[i].submission__submitted_at = years;
                            if (years.toFixed(0) == 1) {
                                vm.leaderboard[i].timeSpan = 'year';
                            } else {
                                vm.leaderboard[i].timeSpan = 'years';
                            }
                        } else if (duration._data.months != 0) {
                            var months = duration.months();
                            vm.leaderboard[i].submission__submitted_at = months;
                            if (months.toFixed(0) == 1) {
                                vm.leaderboard[i].timeSpan = 'month';
                            } else {
                                vm.leaderboard[i].timeSpan = 'months';
                            }
                        } else if (duration._data.days != 0) {
                            var days = duration.asDays();
                            vm.leaderboard[i].submission__submitted_at = days;
                            if (days.toFixed(0) == 1) {
                                vm.leaderboard[i].timeSpan = 'day';
                            } else {
                                vm.leaderboard[i].timeSpan = 'days';
                            }
                        } else if (duration._data.hours != 0) {
                            var hours = duration.asHours();
                            vm.leaderboard[i].submission__submitted_at = hours;
                            if (hours.toFixed(0) == 1) {
                                vm.leaderboard[i].timeSpan = 'hour';
                            } else {
                                vm.leaderboard[i].timeSpan = 'hours';
                            }
                        } else if (duration._data.minutes != 0) {
                            var minutes = duration.asMinutes();
                            vm.leaderboard[i].submission__submitted_at = minutes;
                            if (minutes.toFixed(0) == 1) {
                                vm.leaderboard[i].timeSpan = 'minute';
                            } else {
                                vm.leaderboard[i].timeSpan = 'minutes';
                            }
                        } else if (duration._data.seconds != 0) {
                            var second = duration.asSeconds();
                            vm.leaderboard[i].submission__submitted_at = second;
                            if (second.toFixed(0) == 1) {
                                vm.leaderboard[i].timeSpan = 'second';
                            } else {
                                vm.leaderboard[i].timeSpan = 'seconds';
                            }
                        }
                    }
                    vm.phaseName = vm.phaseSplitId;
                    vm.startLeaderboard();
                    vm.stopLoader();
                    vm.scrollToEntryAfterLeaderboardLoads();
                },
                onError: function(response) {
                    var error = response.data;
                    vm.leaderboard.error = error;
                    vm.stopLoader();
                }
            };

            utilities.sendRequest(parameters);
        };

        if (vm.phaseSplitId) {
            vm.getLeaderboard(vm.phaseSplitId);
        }
        vm.getAllEntries = false;

        // function for toggeling between public leaderboard and complete leaderboard [public/private]
        vm.toggleLeaderboard = function(getAllEntries){
            vm.getAllEntries = getAllEntries;
            if (vm.phaseSplitId) {
                if (vm.getAllEntries){
                    vm.getAllEntriesTestOption = "Exclude private submissions";
                    vm.getAllEntriesOnPublicLeaderboard(vm.phaseSplitId);
                }
                else {
                    vm.getAllEntriesTestOption = "Include private submissions";
                    vm.getLeaderboard(vm.phaseSplitId);
                }
            }
        };

        // function to create new team for participating in challenge
        vm.createNewTeam = function() {
            vm.isLoader = true;
            vm.loaderTitle = '';
            vm.newContainer = angular.element('.new-team-card');

            vm.startLoader("Loading Teams");

            parameters.url = 'participants/participant_team';
            parameters.method = 'POST';
            parameters.data = {
                "team_name": vm.team.name,
                "team_url": vm.team.url
            };
            parameters.callback = {
                onSuccess: function() {
                    $rootScope.notify("success", "Team " + vm.team.name + " has been created successfully!");
                    vm.team.error = false;
                    vm.stopLoader();
                    vm.team = {};

                    vm.startLoader("Loading Teams");
                    parameters.url = 'participants/participant_team';
                    parameters.method = 'GET';
                    parameters.callback = {
                        onSuccess: function(response) {
                            var status = response.status;
                            var details = response.data;
                            if (status == 200) {
                                vm.existTeam = details;
                                vm.showPagination = true;
                                vm.paginationMsg = '';


                                // condition for pagination
                                if (vm.existTeam.next === null) {
                                    vm.isNext = 'disabled';
                                    vm.currentPage = 1;
                                } else {
                                    vm.isNext = '';
                                    vm.currentPage = vm.existTeam.next.split('page=')[1] - 1;
                                }

                                if (vm.existTeam.previous === null) {
                                    vm.isPrev = 'disabled';
                                } else {
                                    vm.isPrev = '';
                                }


                                vm.stopLoader();
                            }
                        },
                        onError: function() {
                            vm.stopLoader();
                        }
                    };
                    utilities.sendRequest(parameters);
                },
                onError: function(response) {
                    var error = response.data;
                    vm.team.error = error.team_name[0];
                    vm.stopLoader();
                    $rootScope.notify("error", "New team couldn't be created.");
                }
            };

            utilities.sendRequest(parameters);
        };

        vm.getAllSubmissionResults = function(phaseId) {
            vm.stopFetchingSubmissions = function() {
                $interval.cancel(vm.poller);
            };

            vm.stopFetchingSubmissions();
            vm.isResult = true;
            if (phaseId !== undefined) {
                vm.phaseId = phaseId;
            }

            // loader for loading submissions.
            vm.startLoader = loaderService.startLoader;
            vm.startLoader("Loading Submissions");

            // get submissions of all the challenge phases
            vm.isNext = '';
            vm.isPrev = '';
            vm.currentPage = '';
            vm.showPagination = false;
            if (vm.filter_all_submission_by_team_name === '') {
                parameters.url = "challenges/" + vm.challengeId + "/challenge_phase/" +
                vm.phaseId + "/submissions";
            } else {
                parameters.url = "challenges/" + vm.challengeId + "/challenge_phase/" +
                vm.phaseId + "/submissions?participant_team__team_name=" + vm.filter_all_submission_by_team_name;
            }
            parameters.method = 'GET';
            parameters.data = {};
            parameters.callback = {
                onSuccess: function(response) {
                    var details = response.data;
                    vm.submissionResult = details;

                    if (Array.isArray(vm.submissionResult.results)) {
                        for (var i = 0; i < details.results.length; i++) {
                            vm.submissionVisibility[details.results[i].id] = details.results[i].is_public;
                            vm.verifiedStatus[details.results[i].id] = details.results[i].is_verified_by_host;
                        }
                    }

                    if (vm.submissionResult.count === 0) {
                        vm.showPagination = false;
                        vm.paginationMsg = "No results found";
                    } else {
                        vm.showPagination = true;
                        vm.paginationMsg = "";
                    }

                    if (vm.submissionResult.next === null) {
                        vm.isNext = 'disabled';
                    } else {
                        vm.isNext = '';

                    }
                    if (vm.submissionResult.previous === null) {
                        vm.isPrev = 'disabled';
                    } else {
                        vm.isPrev = '';
                    }
                    if (vm.submissionResult.next !== null) {
                        vm.currentPage = vm.submissionResult.next.split('page=')[1] - 1;
                        vm.currentRefPage = Math.ceil(vm.currentPage);
                    } else {
                        vm.currentPage = 1;
                        vm.currentRefPage = Math.ceil(vm.currentPage);
                    }

                    vm.load = function(url) {
                        // loader for loading submissions
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
                                    vm.currentPage = vm.submissionResult.count / 150;
                                    vm.currentRefPage = Math.ceil(vm.currentPage);
                                } else {
                                    vm.isNext = '';
                                    vm.currentPage = parseInt(vm.submissionResult.next.split('page=')[1] - 1);
                                    vm.currentRefPage = Math.ceil(vm.currentPage);
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
                    };
                    vm.stopLoader();
                },
                onError: function(response) {
                    var error = response.data;
                    utilities.storeData('emailError', error.detail);
                    $state.go('web.permission-denied');
                    vm.stopLoader();
                }
            };
            utilities.sendRequest(parameters);
        };

        vm.changeSubmissionVisibility = function(submission_id, submissionVisibility) {
            parameters.url = "jobs/challenge/" + vm.challengeId + "/challenge_phase/" + vm.phaseId + "/submission/" + submission_id;
            parameters.method = 'PATCH';
            parameters.data = {
                "is_public": submissionVisibility
            };
            parameters.callback = {
                onSuccess: function(response) {
                    var status = response.status;
                    var message = "";
                    if (status === 200) {
                      var detail = response.data;
                      if (detail['is_public'] == true) {
                        message = "The submission is made public.";
                      }
                      else {
                        message = "The submission is made private.";
                      }
                      $rootScope.notify("success", message);
                      if (vm.isCurrentPhaseRestrictedToSelectOneSubmission) {
                        $mdDialog.hide();
                        if (vm.previousPublicSubmissionId != submission_id) {
                            vm.submissionVisibility[vm.previousPublicSubmissionId] = false;
                            vm.previousPublicSubmissionId = submission_id;
                        } else {
                            vm.previousPublicSubmissionId = null;
                        }
                        vm.submissionVisibility[submission_id] = submissionVisibility;
                      }
                    }
                },
                onError: function(response) {
                    var error = response.data;
                    var status = response.status;
                    if (status === 400 || status === 403) {
                       $rootScope.notify("error", error.error);
                    }
                    if (vm.isCurrentPhaseRestrictedToSelectOneSubmission) {
                       $mdDialog.hide();
                       vm.submissionVisibility[submission_id] = !vm.submissionVisibility[submission_id];
                    }
                }
            };
            utilities.sendRequest(parameters);
        };

        vm.changeBaselineStatus = function(submission_id) {
            parameters.url = "jobs/challenge/" + vm.challengeId + "/challenge_phase/" + vm.phaseId + "/submission/" + submission_id;
            parameters.method = 'PATCH';
            parameters.data = {
                "is_baseline": vm.baselineStatus[submission_id]
            };
            parameters.callback = {
                onSuccess: function() {},
                onError: function() {}
            };

            utilities.sendRequest(parameters);
        };

        vm.showRemainingSubmissions = function(phaseID) {
            vm.remainingSubmissions = {};
            vm.remainingTime = {};
            vm.showClock = false;
            vm.showSubmissionNumbers = false;
            vm.maxExceeded = false;
            parameters.url = "jobs/" + vm.challengeId + "/remaining_submissions/";
            parameters.method = 'GET';
            parameters.callback = {
                onSuccess: function(response) {
                    var status = response.status;
                    for (var phase in response.data.phases) {
                        if (response.data.phases[phase].id == phaseID) {
                           var details = response.data.phases[phase].limits;
                        }
                    }
                    if (status === 200) {
                        if (details.submission_limit_exceeded === true) {
                            vm.maxExceeded = true;
                            vm.maxExceededMessage = details.message;
                            vm.disableSubmit = true;
                        }
                        else if (details.remaining_submissions_today_count > 0) {
                            vm.remainingSubmissions = details;
                            vm.showSubmissionNumbers = true;
                            vm.disableSubmit = false;
                        } else {
                            vm.message = details;
                            vm.showClock = true;
                            vm.disableSubmit = true;
                            vm.countDownTimer = function() {
                                vm.remainingTime = vm.message.remaining_time;
                                vm.days = Math.floor(vm.remainingTime / 24 / 60 / 60);
                                vm.hoursLeft = Math.floor((vm.remainingTime) - (vm.days * 86400));
                                vm.hours = Math.floor(vm.hoursLeft / 3600);
                                vm.minutesLeft = Math.floor((vm.hoursLeft) - (vm.hours * 3600));
                                vm.minutes = Math.floor(vm.minutesLeft / 60);
                                vm.remainingSeconds = Math.floor(vm.remainingTime % 60);
                                if (vm.remainingSeconds < 10) {
                                    vm.remainingSeconds = "0" + vm.remainingSeconds;
                                }
                                if (vm.remainingTime === 0) {
                                    vm.showSubmissionNumbers = true;
                                } else {
                                    vm.remainingSeconds--;
                                }
                            };
                            setInterval(function() {
                                $rootScope.$apply(vm.countDownTimer);
                            }, 1000);
                            vm.countDownTimer();
                        }
                    }
                },
                onError: function(response) {
                    var details = response.data;
                    vm.stopLoader();
                    $rootScope.notify("error", details.error);
                }
            };
            utilities.sendRequest(parameters);
        };

        vm.fileTypes = [{ 'name': 'csv' }];
        vm.fields = [{
            'label': 'Team Name',
            'id': 'participant_team'
        },{
            'label': 'Team Members',
            'id': 'participant_team_members'
        },{
            'label': 'Team Members Email Id',
            'id': 'participant_team_members_email'
        },{
            'label': 'Team Members Affiliation',
            'id': 'participant_team_members_affiliation'
        },{
            'label': 'Challenge Phase',
            'id': 'challenge_phase'
        },{
            'label': 'Status',
            'id': 'status'
        },{
            'label': 'Created By',
            'id': 'created_by'
        },{
            'label': 'Execution Time',
            'id': 'execution_time'
        },{
            'label': 'Submission Number',
            'id': 'submission_number'
        },{
            'label': 'Submitted File',
            'id': 'input_file'
        },{
            'label': 'Stdout File',
            'id': 'stdout_file'
        },{
            'label': 'Stderr File',
            'id': 'stderr_file'
        },{
            'label': 'Submitted At',
            'id': 'created_at'
        },{
            'label': 'Submission Result File',
            'id': 'submission_result_file'
        },{
            'label': 'Submission Metadata File',
            'id': 'submission_metadata_file'
        },{
            'label': 'Method Name',
            'id': 'method_name'
        },{
            'label': 'Method Description',
            'id': 'method_description'
        },{
            'label': 'Publication URL',
            'id': 'publication_url'
        },{
            'label': 'Project URL',
            'id': 'project_url'
        },{
            'label': 'Submission Meta Attributes',
            'id': 'submission_meta_attributes'
        }];

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
            }
        };

        vm.isOptionChecked = function (option, attribute) {
            if(
                attribute.values.findIndex((el) => {
                    return el===option;
                }) !== -1
            ) {
                return true;
            }
            return false;
        };

        vm.showMdDialog = function (ev, submissionId) {
            for (var i = 0; i < vm.submissionResult.count; i++) {
                if (vm.submissionResult.results[i].id === submissionId) {
                    vm.submissionMetaData = vm.submissionResult.results[i];
                    break;
                }
            }
            vm.method_name = vm.submissionMetaData.method_name;
            vm.method_description = vm.submissionMetaData.method_description;
            vm.project_url = vm.submissionMetaData.project_url;
            vm.publication_url = vm.submissionMetaData.publication_url;
            vm.submissionId = submissionId;
            if (vm.submissionMetaData.submission_metadata != null) {
                vm.currentSubmissionMetaData = JSON.parse(JSON.stringify(vm.submissionMetaData.submission_metadata));
            }
            $mdDialog.show({
                scope: $scope,
                preserveScope: true,
                targetEvent: ev,
                templateUrl: 'dist/views/web/challenge/update-submission-metadata.html',
            });
        };

        vm.showVisibilityDialog = function(submissionId, submissionVisibility) {
            vm.submissionId = submissionId;
            // Show modal only when submission is being made public
            if (submissionVisibility) {
                // Show pop up only when there's a submission already selected
                if (vm.previousPublicSubmissionId) {
                    $mdDialog.show({
                        scope: $scope,
                        preserveScope: true,
                        templateUrl: 'dist/views/web/challenge/update-submission-visibility.html'
                    });
                } else {
                    vm.changeSubmissionVisibility(submissionId, submissionVisibility);
                }
            } else {
                // Case when a submission is made private
                vm.changeSubmissionVisibility(submissionId, submissionVisibility);
            }
        };

        vm.cancelSubmission = function(submissionId) {
            parameters.url = "jobs/challenges/" + vm.challengeId + "/submissions/" + submissionId + "/update_submission_meta/";
            parameters.method = 'PATCH';
            parameters.data = {
                "status": "cancelled",
            };
            parameters.callback = {
                onSuccess: function(response) {
                    var status = response.status;
                    if (status === 200) {
                        $mdDialog.hide();
                        $rootScope.notify("success", "Submission cancelled successfully!");
                    }
                },
                onError: function(response) {
                    $mdDialog.hide();
                    var error = response.data;
                    $rootScope.notify("error", error);
                }
            };

            utilities.sendRequest(parameters);
        };

        vm.showCancelSubmissionDialog = function(submissionId, status) {
            if (status != "submitted") {
                $rootScope.notify("error", "Only unproccessed submissions can be cancelled");
                return;
            }
            vm.submissionId = submissionId;
            $mdDialog.show({
                scope: $scope,
                preserveScope: true,
                templateUrl: 'dist/views/web/challenge/cancel-submission.html'
            });
        };

        vm.hideDialog = function() {
            $mdDialog.hide();
        };

        vm.updateSubmissionMetaData = function(updateSubmissionMetaDataForm) {
            if (updateSubmissionMetaDataForm) {
                parameters.url = "jobs/challenge/" + vm.challengeId + "/challenge_phase/" + vm.phaseId + "/submission/" + vm.submissionId;
                parameters.method = 'PATCH';
                parameters.data = {
                    "method_name": vm.method_name,
                    "method_description": vm.method_description,
                    "project_url": vm.project_url,
                    "publication_url": vm.publication_url,
                    "submission_metadata": vm.currentSubmissionMetaData
                };
                parameters.callback = {
                    onSuccess: function(response) {
                        var status = response.status;
                        if (status === 200) {
                            $mdDialog.hide();
                            $rootScope.notify("success", "The data is successfully updated!");
                            if(vm.currentSubmissionMetaData != null) {
                                vm.submissionMetaData.submission_metadata = JSON.parse(JSON.stringify(vm.currentSubmissionMetaData));
                            }
                        }
                    },
                    onError: function(response) {
                        $mdDialog.hide();
                        var error = response.data;
                        $rootScope.notify("error", error);
                    }
                };

                utilities.sendRequest(parameters);
            } else {
                $mdDialog.hide();
            }
        };

        vm.verifySubmission = function(submissionId, isVerified) {
            parameters.url = "jobs/challenges/" + vm.challengeId + "/submissions/" + submissionId + "/update_submission_meta/";
            parameters.method = 'PATCH';
            parameters.data = {
                "is_verified_by_host": isVerified,
            };
            parameters.callback = {
                onSuccess: function(response) {
                    var status = response.status;
                    if (status === 200) {
                        $rootScope.notify("success", "Verification status updated successfully!");
                    }
                },
                onError: function(response) {
                    var error = response.data;
                    $rootScope.notify("error", error);
                }
            };
            utilities.sendRequest(parameters);
        };

        vm.isStarred = function() {
            // Get the stars count and user specific starred or unstarred
            parameters.url = "challenges/" + vm.challengeId + "/";
            parameters.method = 'GET';
            parameters.data = {};
            parameters.callback = {
                onSuccess: function(response) {
                    var details = response.data;
                    vm.count = details['count'] || 0;
                    vm.is_starred = details['is_starred'];
                    if (details['is_starred'] === false) {
                        vm.caption = 'Star';
                    } else {
                        vm.caption = 'Unstar';
                    }
                },
                onError: function() {}
            };
            utilities.sendRequest(parameters);
        };

        vm.starChallenge = function() {
            parameters.url = "challenges/" + vm.challengeId + "/";
            parameters.method = 'POST';
            parameters.data = {};
            parameters.callback = {
                onSuccess: function(response) {
                    var details = response.data;
                    vm.count = details['count'];
                    vm.is_starred = details['is_starred'];
                    if (details.is_starred === true) {
                        vm.caption = 'Unstar';
                    } else {
                        vm.caption = 'Star';
                    }
                },
                onError: function(response) {
                    var error = response.data;
                    $rootScope.notify("error", error);
                }
            };
            utilities.sendRequest(parameters);
        };

        // Edit challenge overview
        vm.overviewDialog = function(ev) {
            vm.tempDesc = vm.page.description;
            $mdDialog.show({
                scope: $scope,
                preserveScope: true,
                targetEvent: ev,
                templateUrl: 'dist/views/web/challenge/edit-challenge/edit-challenge-overview.html',
                escapeToClose: false
            });
        };

        vm.editChallengeOverview = function(editChallengeOverviewForm) {
            if (editChallengeOverviewForm) {
                var challengeHostList = utilities.getData("challengeCreator");
                for (var challenge in challengeHostList) {
                    if (challenge == vm.challengeId) {
                        vm.challengeHostId = challengeHostList[challenge];
                        break;
                    }
                }
                parameters.url = "challenges/challenge_host_team/" + vm.challengeHostId + "/challenge/" + vm.challengeId;
                parameters.method = 'PATCH';
                parameters.data = {
                    "description": vm.page.description

                };
                parameters.callback = {
                    onSuccess: function(response) {
                        var status = response.status;
                        if (status === 200) {
                            $mdDialog.hide();
                            $rootScope.notify("success", "The description is successfully updated!");
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
            } else {
                vm.page.description = vm.tempDesc;
                $mdDialog.hide();
            }
        };

        // Delete challenge
        vm.deleteChallengeDialog = function(ev) {
            vm.titleInput = "";
            $mdDialog.show({
                scope: $scope,
                preserveScope: true,
                targetEvent: ev,
                templateUrl: 'dist/views/web/challenge/delete-challenge/delete-challenge.html',
                escapeToClose: false
            });
        };

        vm.deleteChallenge = function(deleteChallengeForm) {
            if (deleteChallengeForm){
                var parameters = {};
                parameters.url = "challenges/challenge/" + vm.challengeId + "/disable";
                parameters.method = 'POST';
                parameters.token = userKey;
                parameters.callback = {
                    onSuccess: function(response) {
                        var status = response.status;
                        if (status === 204){
                            $mdDialog.hide();
                            $rootScope.notify("success", "The Challenge is successfully deleted!");
                        }
                    },
                    onError: function(response) {
                        $mdDialog.hide();
                        var error = response.data;
                        $rootScope.notify("error", error);
                    }
                };

                utilities.sendRequest(parameters);
            } else {
                $mdDialog.hide();
            }
        };

        // Edit submission guidelines
        vm.submissionGuidelinesDialog = function(ev) {
            vm.tempSubmissionGuidelines = vm.page.submission_guidelines;
            $mdDialog.show({
                scope: $scope,
                preserveScope: true,
                targetEvent: ev,
                templateUrl: 'dist/views/web/challenge/edit-challenge/edit-challenge-submission-guidelines.html',
                escapeToClose: false
            });
        };

        vm.editSubmissionGuideline = function(editSubmissionGuidelinesForm) {
            if (editSubmissionGuidelinesForm) {
                var challengeHostList = utilities.getData("challengeCreator");
                for (var challenge in challengeHostList) {
                    if (challenge == vm.challengeId) {
                        vm.challengeHostId = challengeHostList[challenge];
                        break;
                    }
                }
                parameters.url = "challenges/challenge_host_team/" + vm.challengeHostId + "/challenge/" + vm.challengeId;
                parameters.method = 'PATCH';
                parameters.data = {
                    "submission_guidelines": vm.page.submission_guidelines

                };
                parameters.callback = {
                    onSuccess: function(response) {
                        var status = response.status;
                        if (status === 200) {
                            $mdDialog.hide();
                            $rootScope.notify("success", "The submission guidelines is successfully updated!");
                        }
                    },
                    onError: function(response) {
                        $mdDialog.hide();
                        vm.page.submission_guidelines = vm.tempSubmissionGuidelines;
                        var error = response.data;
                        $rootScope.notify("error", error);
                    }
                };

                utilities.sendRequest(parameters);
            } else {
                vm.page.submission_guidelines = vm.tempSubmissionGuidelines;
                $mdDialog.hide();
            }
        };

        // Edit Evaluation Criteria
        vm.evaluationCriteriaDialog = function(ev) {
            vm.tempEvaluationCriteria = vm.page.evaluation_details;
            $mdDialog.show({
                scope: $scope,
                preserveScope: true,
                targetEvent: ev,
                templateUrl: 'dist/views/web/challenge/edit-challenge/edit-challenge-evaluation-criteria.html',
                escapeToClose: false
            });
        };

        vm.editEvaluationCriteria = function(editEvaluationCriteriaForm) {
            if (editEvaluationCriteriaForm) {
                var challengeHostList = utilities.getData("challengeCreator");
                for (var challenge in challengeHostList) {
                    if (challenge == vm.challengeId) {
                        vm.challengeHostId = challengeHostList[challenge];
                        break;
                    }
                }
                parameters.url = "challenges/challenge_host_team/" + vm.challengeHostId + "/challenge/" + vm.challengeId;
                parameters.method = 'PATCH';
                parameters.data = {
                    "evaluation_details": vm.page.evaluation_details
                };
                parameters.callback = {
                    onSuccess: function(response) {
                        var status = response.status;
                        if (status === 200) {
                            $mdDialog.hide();
                            $rootScope.notify("success", "The evaluation details is successfully updated!");
                        }
                    },
                    onError: function(response) {
                        $mdDialog.hide();
                        vm.page.evaluation_details = vm.tempEvaluationCriteria;
                        var error = response.data;
                        $rootScope.notify("error", error);
                    }
                };

                utilities.sendRequest(parameters);

            } else {
                vm.page.evaluation_details = vm.tempEvaluationCriteria;
                $mdDialog.hide();
            }
        };


        // Edit Evaluation Script
        vm.evaluationScriptDialog = function(ev) {
            vm.tempEvaluationCriteria = vm.page.evaluation_details;
            $mdDialog.show({
                scope: $scope,
                preserveScope: true,
                targetEvent: ev,
                templateUrl: 'dist/views/web/challenge/edit-challenge/edit-challenge-evaluation-script.html',
                escapeToClose: false
            });
        };

        vm.editEvalScript = function(editEvaluationCriteriaForm) {
            if (editEvaluationCriteriaForm) {
                if (vm.editEvaluationScript === undefined || vm.editEvaluationScript === null
                     || vm.editEvaluationScript === "") {
                    var error = "Please upload a valid evaluation script!";
                    $mdDialog.hide();
                    $rootScope.notify("error", error);
                    return;
                }
                var formData = new FormData();
                formData.append("evaluation_script", vm.editEvaluationScript);
                var challengeHostList = utilities.getData("challengeCreator");
                for (var challenge in challengeHostList) {
                    if (challenge == vm.challengeId) {
                        vm.challengeHostId = challengeHostList[challenge];
                        break;
                    }
                }
                parameters.url = "challenges/challenge_host_team/" + vm.challengeHostId + "/challenge/" + vm.challengeId;
                parameters.method = 'PATCH';
                parameters.data = formData;
                parameters.callback = {
                    onSuccess: function(response) {
                        var status = response.status;
                        if (status === 200) {
                            $mdDialog.hide();
                            $rootScope.notify("success", "The evaluation script is successfully updated!");
                        }
                    },
                    onError: function(response) {
                        $mdDialog.hide();
                        vm.page.evaluation_details = vm.tempEvaluationCriteria;
                        var error = response.data;
                        $rootScope.notify("error", error);
                    }
                };

                utilities.sendRequest(parameters, 'header', 'upload');

            } else {
                vm.page.evaluation_details = vm.tempEvaluationCriteria;
                $mdDialog.hide();
            }
        };


        // Edit Terms and Conditions
        vm.termsAndConditionsDialog = function(ev) {
            vm.tempTermsAndConditions = vm.page.terms_and_conditions;
            $mdDialog.show({
                scope: $scope,
                preserveScope: true,
                targetEvent: ev,
                templateUrl: 'dist/views/web/challenge/edit-challenge/edit-challenge-terms-and-conditions.html',
                escapeToClose: false
            });
        };

        vm.editTermsAndConditions = function(editTermsAndConditionsForm) {
            if (editTermsAndConditionsForm) {
                var challengeHostList = utilities.getData("challengeCreator");
                for (var challenge in challengeHostList) {
                    if (challenge == vm.challengeId) {
                        vm.challengeHostId = challengeHostList[challenge];
                        break;
                    }
                }
                parameters.url = "challenges/challenge_host_team/" + vm.challengeHostId + "/challenge/" + vm.challengeId;
                parameters.method = 'PATCH';
                parameters.data = {
                    "terms_and_conditions": vm.page.terms_and_conditions
                };
                parameters.callback = {
                    onSuccess: function(response) {
                        var status = response.status;
                        if (status === 200) {
                            $mdDialog.hide();
                            $rootScope.notify("success", "The terms and conditions are successfully updated!");
                        }
                    },
                    onError: function(response) {
                        $mdDialog.hide();
                        vm.page.terms_and_conditions = vm.tempTermsAndConditions;
                        var error = response.data;
                        $rootScope.notify("error", error);
                    }
                };
                utilities.sendRequest(parameters);
            } else {
                vm.page.terms_and_conditions = vm.tempTermsAndConditions;
                $mdDialog.hide();
            }
        };

        // Edit Challenge Title
        vm.challengeTitleDialog = function(ev) {
            vm.tempChallengeTitle = vm.page.title;
            $mdDialog.show({
                scope: $scope,
                preserveScope: true,
                targetEvent: ev,
                templateUrl: 'dist/views/web/challenge/edit-challenge/edit-challenge-title.html',
                escapeToClose: false
            });
        };

        vm.editChallengeTitle = function(editChallengeTitleForm) {
            if (editChallengeTitleForm) {
                var challengeHostList = utilities.getData("challengeCreator");
                for (var challenge in challengeHostList) {
                    if (challenge == vm.challengeId) {
                        vm.challengeHostId = challengeHostList[challenge];
                        break;
                    }
                }
                parameters.url = "challenges/challenge_host_team/" + vm.challengeHostId + "/challenge/" + vm.challengeId;
                parameters.method = 'PATCH';
                parameters.data = {
                    "title": vm.page.title
                };
                parameters.callback = {
                    onSuccess: function(response) {
                        var status = response.status;
                        if (status === 200) {
                            $mdDialog.hide();
                            $rootScope.notify("success", "The challenge title is  successfully updated!");
                        }
                    },
                    onError: function(response) {
                        $mdDialog.hide();
                        vm.page.title = vm.tempChallengeTitle;
                        var error = response.data;
                        $rootScope.notify("error", error);
                    }
                };
                utilities.sendRequest(parameters);
            } else {
                vm.page.title = vm.tempChallengeTitle;
                $mdDialog.hide();
            }
        };

        vm.challengePhaseDialog = function(ev, phase) {
            vm.page.challenge_phase = phase;
            vm.page.max_submissions_per_day = phase.max_submissions_per_day;
            vm.page.max_submissions_per_month = phase.max_submissions_per_month;
            vm.phaseStartDate = moment(phase.start_date);
            vm.phaseEndDate = moment(phase.end_date);
            vm.testAnnotationFile = null;
            vm.sanityCheckPass = true;
            vm.sanityCheck = "";
            $mdDialog.show({
                scope: $scope,
                preserveScope: true,
                targetEvent: ev,
                templateUrl: 'dist/views/web/challenge/edit-challenge/edit-challenge-phase.html',
                escapeToClose: false
            });
        };

        vm.editChallengePhase = function(editChallengePhaseForm) {
            if (editChallengePhaseForm) {
                vm.challengePhaseId = vm.page.challenge_phase.id;
                parameters.url = "challenges/challenge/" + vm.challengeId + "/challenge_phase/" + vm.challengePhaseId;
                parameters.method = 'PATCH';
                var formData = new FormData();
                formData.append("name", vm.page.challenge_phase.name);
                formData.append("description", vm.page.challenge_phase.description);
                formData.append("start_date", vm.phaseStartDate.toISOString());
                formData.append("end_date", vm.phaseEndDate.toISOString());
                formData.append("max_submissions_per_day", vm.page.challenge_phase.max_submissions_per_day);
                formData.append("max_submissions_per_month", vm.page.challenge_phase.max_submissions_per_month);
                formData.append("max_submissions", vm.page.challenge_phase.max_submissions);
                formData.append("max_concurrent_submissions_allowed", vm.page.challenge_phase.max_concurrent_submissions_allowed); 
                if (vm.testAnnotationFile) {
                    formData.append("test_annotation", vm.testAnnotationFile);
                }
                parameters.data = formData;
                parameters.callback = {
                    onSuccess: function(response) {
                        var status = response.status;
                        utilities.hideLoader();
                        if (status === 200) {
                            $mdDialog.hide();
                            $rootScope.notify("success", "The challenge phase details are successfully updated!");
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
                utilities.sendRequest(parameters, 'header', 'upload');
            } else {
                parameters.url = 'challenges/challenge/' + vm.challengeId + '/challenge_phase';
                parameters.method = 'GET';
                parameters.data = {};
                parameters.callback = {
                    onSuccess: function(response) {
                        var details = response.data;
                        vm.phases = details;
                        utilities.hideLoader();
                    },
                    onError: function(response) {
                        var error = response.data;
                        utilities.storeData('emailError', error.detail);
                        $state.go('web.permission-denied');
                        utilities.hideLoader();
                    }
                };
                utilities.sendRequest(parameters);
                $mdDialog.hide();
            }
        };

        vm.publishChallenge = function(ev) {
            ev.stopPropagation();
            vm.toggleChallengeState = null;
            vm.publishDesc = null;
            if (vm.isPublished)
                vm.toggleChallengeState = "private";
            else
                vm.toggleChallengeState = "public";

            var confirm = $mdDialog.confirm()
                          .title('Make this challenge ' + vm.toggleChallengeState + '?')
                          .ariaLabel('')
                          .targetEvent(ev)
                          .ok('Yes')
                          .cancel('No');

            $mdDialog.show(confirm).then(function() {
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
            vm.stopLoadingLogs();
        });

        $rootScope.$on('$stateChangeStart', function() {
            vm.phase = {};
            vm.isResult = false;
            vm.stopFetchingSubmissions();
            vm.stopLeaderboard();
        });

        vm.showConfirmation = function(message){
            $rootScope.notify("success", message);
        };

        vm.termsAndConditionDialog = function (ev) {
            $mdDialog.show({
                scope: $scope,
                preserveScope: true,
                targetEvent: ev,
                templateUrl: 'dist/views/web/challenge/terms-and-conditions.html',
                escapeToClose: false
            });
        };

        vm.acceptTermsAndConditions = function (acceptTermsAndConditionsForm) {
            if (acceptTermsAndConditionsForm) {
                if (vm.termsAndConditions) {
                    vm.selectExistTeam();
                    $mdDialog.hide();
                }
            } else {
                $mdDialog.hide();
            }
        };

        vm.encodeMetricURI = function(metric) {
            return encodeURIComponent(metric);
        };

    }

})();
