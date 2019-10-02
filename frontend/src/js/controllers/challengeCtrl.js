// Invoking IIFE for challenge page
(function() {

    'use strict';
    angular
        .module('evalai')
        .controller('ChallengeCtrl', ChallengeCtrl);

    ChallengeCtrl.$inject = ['utilities', 'loaderService', '$scope', '$state', '$http', '$stateParams', '$rootScope', 'Upload', '$interval', '$mdDialog', 'moment', '$location', '$anchorScroll', '$timeout'];

    function ChallengeCtrl(utilities, loaderService, $scope, $state, $http, $stateParams, $rootScope, Upload, $interval, $mdDialog, moment, $location, $anchorScroll, $timeout) {
        var vm = this;
        var slugUrl = $stateParams.challengeSlug;
        if (slugUrl !== undefined) {
            vm.challengeId = slugUrl.split("-").pop();
        }
        vm.phaseId = null;
        vm.phaseSplitId = $stateParams.phaseSplitId;
        vm.input_file = null;
        vm.fileUrl = "";
        vm.methodName = "";
        vm.methodDesc = "";
        vm.projectUrl = "";
        vm.publicationUrl = "";
        vm.wrnMsg = {};
        vm.page = {};
        vm.isParticipated = false;
        vm.isActive = false;
        vm.phases = {};
        vm.phaseSplits = {};
        vm.selectedPhaseSplit = {};
        vm.phaseRemainingSubmissions = {};
        vm.phaseRemainingSubmissionsFlags = {};
        vm.phaseRemainingSubmissionsCountdown = {};
        vm.isValid = {};
        vm.submissionVisibility = {};
        vm.baselineStatus = {};
        vm.showUpdate = false;
        vm.showLeaderboardUpdate = false;
        vm.poller = null;
        vm.isChallengeHost = false;
        vm.isDockerBased = false;
        vm.stopLeaderboard = function() {};
        vm.stopFetchingSubmissions = function() {};
        vm.currentDate = null;
        vm.isPublished = false;
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

        vm.filter_all_submission_by_team_name = '';
        vm.filter_my_submission_by_team_name = '';
        // show loader
        vm.startLoader = loaderService.startLoader;
        // stop loader
        vm.stopLoader = loaderService.stopLoader;

        var userKey = utilities.getData('userKey');
        vm.authToken = userKey;

        vm.subErrors = {};

        utilities.showLoader();

        // scroll to the selected entry after page has been rendered
        vm.scrollToEntryAfterLeaderboardLoads = function () {
            // get unique rank number from the url & if exists hightlight the entry
            $timeout(function() {
                const elementId = $location.absUrl().split('?')[0].split('#')[1];
                if (elementId) {
                    $anchorScroll.yOffset = 90;
                    $anchorScroll(elementId);
                    $scope.isHighlight = elementId.split("leaderboardrank-")[1];
                }
            }, 500);
        };
      
        // scroll to the specific entry of the leaderboard
        vm.scrollToSpecificEntryLeaderboard = function (elementId) {
            var newHash = elementId.toString();
            if ($location.hash() !== newHash) {
                $location.hash(elementId);
            } else {
                $anchorScroll();
            }
            $scope.isHighlight = false;
            $anchorScroll.yOffset = 90;
        }

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

                                                // loader for exisiting teams
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
                                                // loader for exisiting teams
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

        vm.makeSubmission = function() {
            if (vm.isParticipated) {
                var fileVal = angular.element(".file-path").val();
                if ((fileVal === null || fileVal === "") && (vm.fileUrl === null || vm.fileUrl === "")) {
                    vm.subErrors.msg = "Please upload file or enter submission URL!";
                } else {
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
                    } else {
                        formData.append("input_file", vm.input_file);
                    }
                    formData.append("status", "submitting");
                    formData.append("method_name", vm.methodName);
                    formData.append("method_description", vm.methodDesc);
                    formData.append("project_url", vm.projectUrl);
                    formData.append("publication_url", vm.publicationUrl);

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
                            $rootScope.notify("success", "Your submission has been recorded succesfully!");
                            vm.disableSubmit = true;
                            vm.showSubmissionNumbers = false;
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
                
                // navigate to challenge page
                // $state.go('web.challenge-page.overview');
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
                for(var i=0; i<details.length; i++) {
                    if (details[i].visibility !== challengePhaseVisibility.public) {
                        vm.phaseSplits[i].showPrivate = true;
                    }
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

        // my submissions
        vm.isResult = false;

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

        vm.getLeaderboard = function(phaseSplitId) {
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

            // get the selected phase split object
            parameters.url = "challenges/challenge/create/challenge_phase_split/" + vm.phaseSplitId + "/";
            parameters.method = "GET";
            parameters.data = {};
            parameters.callback = {
                onSuccess: function (response) {
                    vm.selectedPhaseSplit = response.data;
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
            parameters.url = "jobs/" + "challenge_phase_split/" + vm.phaseSplitId + "/leaderboard/?page_size=1000";
            parameters.method = 'GET';
            parameters.data = {};
            parameters.callback = {
                onSuccess: function(response) {
                    var details = response.data;
                    vm.leaderboard = details.results;
                    for (var i=0; i<vm.leaderboard.length; i++) {
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

            // loader for exisiting teams
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
                    } else {
                        vm.currentPage = 1;
                    }

                    vm.load = function(url) {
                        // loader for exisiting teams
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
                    } else {
                        vm.currentPage = 1;
                    }


                    // Set the is_public flag corresponding to each submission
                    for (var i = 0; i < details.results.length; i++) {
                        vm.submissionVisibility[details.results[i].id] = details.results[i].is_public;
                        vm.baselineStatus[details.results[i].id] = details.results[i].is_baseline;
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

        vm.refreshLeaderboard = function() {
            vm.startLoader("Loading Leaderboard Items");
            vm.leaderboard = {};
            parameters.url = "jobs/" + "challenge_phase_split/" + vm.phaseSplitId + "/leaderboard/?page_size=1000";
            parameters.method = 'GET';
            parameters.data = {};
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
                    } else {
                        vm.currentPage = 1;
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

        vm.changeSubmissionVisibility = function(submission_id) {
            parameters.url = "jobs/challenge/" + vm.challengeId + "/challenge_phase/" + vm.phaseId + "/submission/" + submission_id;
            parameters.method = 'PATCH';
            parameters.data = {
                "is_public": vm.submissionVisibility[submission_id]
            };
            parameters.callback = {
                onSuccess: function(response) {
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
                onError: function(response) {
                    var error = response.data;
                    var status = response.status;
                    if(status === 400 || status === 403 ) {
                       $rootScope.notify("error", error.error);
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

        vm.showMdDialog = function(ev, submissionId) {
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

            $mdDialog.show({
                scope: $scope,
                preserveScope: true,
                targetEvent: ev,
                templateUrl: 'dist/views/web/challenge/update-submission-metadata.html'
            });
        };

        vm.updateSubmissionMetaData = function(updateSubmissionMetaDataForm) {
            if (updateSubmissionMetaDataForm) {
                parameters.url = "jobs/challenge/" + vm.challengeId + "/challenge_phase/" + vm.phaseId + "/submission/" + vm.submissionId;
                parameters.method = 'PATCH';
                parameters.data = {
                    "method_name": vm.method_name,
                    "method_description": vm.method_description,
                    "project_url": vm.project_url,
                    "publication_url": vm.publication_url
                };
                parameters.callback = {
                    onSuccess: function(response) {
                        var status = response.status;
                        if (status === 200) {
                            $mdDialog.hide();
                            $rootScope.notify("success", "The data is successfully updated!");
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
            if(deleteChallengeForm){
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
            vm.phaseStartDate = phase.start_date;
            vm.phaseStartDate = moment(vm.phaseStartDate);
            vm.phaseEndDate = phase.end_date;
            vm.phaseEndDate = moment(vm.phaseEndDate);
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
                formData.append("max_submissions", vm.page.challenge_phase.max_submissions);
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
                          .ok('I\'m sure')
                          .cancel('No.');

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

        
    }

})();
