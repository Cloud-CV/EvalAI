// Invoking IIFE for challenge page
(function() {

    'use strict';
    angular
        .module('evalai')
        .controller('ChallengeCtrl', ChallengeCtrl);

    ChallengeCtrl.$inject = ['utilities', 'loaderService', '$scope', '$state', '$http', '$stateParams', '$rootScope', 'Upload', '$interval', '$mdDialog'];

    function ChallengeCtrl(utilities, loaderService, $scope, $state, $http, $stateParams, $rootScope, Upload, $interval, $mdDialog) {
        var vm = this;
        vm.challengeId = $stateParams.challengeId;
        vm.phaseId = null;
        vm.phaseSplitId = null;
        vm.input_file = null;
        vm.methodName = null;
        vm.methodDesc = null;
        vm.projectUrl = null;
        vm.publicationUrl = null;
        vm.wrnMsg = {};
        vm.page = {};
        vm.isParticipated = false;
        vm.isActive = false;
        vm.phases = {};
        vm.phaseSplits = {};
        vm.isValid = {};
        vm.submissionVisibility = {};
        vm.showUpdate = false;
        vm.showLeaderboardUpdate = false;
        vm.poller = null;
        vm.isChallengeHost = false;
        vm.stopLeaderboard = function() {};
        vm.stopFetchingSubmissions = function() {};
        vm.currentDate = null;


        // loader for existing teams
        vm.isExistLoader = false;
        vm.loaderTitle = '';
        vm.loaderContainer = angular.element('.exist-team-card');

        // show loader
        vm.startLoader =  loaderService.startLoader;
        // stop loader
        vm.stopLoader = loaderService.stopLoader;

        var userKey = utilities.getData('userKey');

        vm.subErrors = {};

        utilities.showLoader();

        // get details of the particular challenge
        var parameters = {};
        parameters.url = 'challenges/challenge/' + vm.challengeId + '/';
        parameters.method = 'GET';
        parameters.data = {};
        parameters.token = userKey;
        parameters.callback = {
            onSuccess: function(response) {
                var details = response.data;
                vm.page = details;
                vm.isActive = details.is_active;


                if (vm.page.image === null) {
                    vm.page.image = "dist/images/logo.png";

                }

                if (vm.isActive) {

                    // get details of challenges corresponding to participant teams of that user
                    var parameters = {};
                    parameters.url = 'participants/participant_teams/challenges/'+ vm.challengeId + '/user';
                    parameters.method = 'GET';
                    parameters.data = {};
                    parameters.token = userKey;
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

                                                var parameters = {};
                                                parameters.url = 'challenges/challenge/' + vm.challengeId + '/participant_team/' + vm.teamId;
                                                parameters.method = 'POST';
                                                parameters.token = userKey;
                                                parameters.callback = {
                                                    onSuccess: function() {
                                                        vm.isParticipated = true;
                                                        $state.go('web.challenge-main.challenge-page.submission');
                                                        vm.stopLoader();
                                                    },
                                                    onError: function(response) {
                                                        if (response.status == 404) {
                                                            var error = "Please select a team first!";
                                                        } else {
                                                            error = "Server error";
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
                            // This condition means that the user is eligible to make submissions
                            // else if (vm.isParticipated) {

                            // }
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
                utilities.storeData('emailError', error.detail);
                $state.go('web.permission-denied');
                utilities.hideLoader();
            }
        };

        utilities.sendRequest(parameters);

        vm.makeSubmission = function() {
            if (vm.isParticipated) {


                var fileVal = angular.element(".file-path").val();

                if (fileVal === null || fileVal === "") {
                    vm.subErrors.msg = "Please upload file!";
                } else {
                    vm.isExistLoader = true;
                    vm.loaderTitle = '';
                    vm.loaderContainer = angular.element('.exist-team-card');


                    vm.startLoader("Making Submission");
                    if (vm.input_file) {
                        // vm.upload(vm.input_file);
                    }
                    var parameters = {};
                    parameters.url = 'jobs/challenge/' + vm.challengeId + '/challenge_phase/' + vm.phaseId + '/submission/';
                    parameters.method = 'POST';
                    var formData = new FormData();
                    formData.append("status", "submitting");
                    formData.append("input_file", vm.input_file);
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


                            vm.phaseId = null;
                            vm.methodName = null;
                            vm.methodDesc = null;
                            vm.projectUrl = null;
                            vm.publicationUrl = null;
                            // vm.subErrors.msg = "Your submission has been recorded succesfully!";
                            $rootScope.notify("success", "Your submission has been recorded succesfully!");

                            vm.stopLoader();
                        },
                        onError: function(response) {
                            var status = response.status;
                            var error = response.data;

                            vm.phaseId = null;
                            vm.methodName = null;
                            vm.methodDesc = null;
                            vm.projectUrl = null;
                            vm.publicationUrl = null;
                            if (status == 404) {

                                vm.subErrors.msg = "Please select phase!";
                            } else if (status == 400) {
                                vm.subErrors.msg = error.input_file[0];
                            } else {
                                vm.subErrors.msg = error.error;
                            }
                            vm.stopLoader();
                        }
                    };

                    utilities.sendRequest(parameters, 'header', 'upload');
                }
            }
        };



        // get details of the particular challenge phase
        parameters = {};
        parameters.url = 'challenges/challenge/' + vm.challengeId + '/challenge_phase';
        parameters.method = 'GET';
        parameters.data = {};
        parameters.token = userKey;
        parameters.callback = {
            onSuccess: function(response) {
                var details = response.data;
                vm.phases = details;
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

        // get details of the particular challenge phase split
        parameters = {};
        parameters.url = 'challenges/' + vm.challengeId + '/challenge_phase_split';
        parameters.method = 'GET';
        parameters.data = {};
        parameters.token = userKey;
        parameters.callback = {
            onSuccess: function(response) {
                var details = response.data;
                vm.phaseSplits = details;
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

        // my submissions
        vm.isResult = false;

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


            // Show leaderboard
            vm.leaderboard = {};
            var parameters = {};
            parameters.url = "jobs/" + "challenge_phase_split/" + vm.phaseSplitId + "/leaderboard/?page_size=1000";
            parameters.method = 'GET';
            parameters.data = {};
            parameters.token = userKey;
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
            vm.startLeaderboard = function() {
                vm.stopLeaderboard();
                vm.poller = $interval(function() {
                    var parameters = {};
                    parameters.url = "jobs/" + "challenge_phase_split/" + vm.phaseSplitId + "/leaderboard/?page_size=1000";
                    parameters.method = 'GET';
                    parameters.data = {};
                    parameters.token = userKey;
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

        };
        vm.getResults = function(phaseId) {

            vm.stopFetchingSubmissions = function() {
                $interval.cancel(vm.poller);
            };
            vm.stopFetchingSubmissions();
            vm.isResult = true;
            vm.phaseId = phaseId;

            var all_phases = vm.phases.results;
            for (var i = 0; i < vm.phases.results.length; i++) {
                if (all_phases[i].id == phaseId) {
                    vm.currentPhaseLeaderboardPublic = all_phases[i].leaderboard_public;
                    break;
                }
            }

            parameters = {};
            parameters.url = "analytics/challenge/" + vm.challengeId + "/challenge_phase/"+ vm.phaseId + "/count";
            parameters.method = 'GET';
            parameters.data = {};
            parameters.token = userKey;
            parameters.callback = {
                onSuccess: function(response) {
                    var details = response.data;
                    vm.submissionCount = details.submissions_count_for_challenge_phase;
                },
                onError: function(response){
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

            var parameters = {};
            parameters.url = "jobs/challenge/" + vm.challengeId + "/challenge_phase/" + vm.phaseId + "/submission/";
            parameters.method = 'GET';
            parameters.data = {};
            parameters.token = userKey;
            parameters.callback = {
                onSuccess: function(response) {
                    var details = response.data;
                    vm.submissionResult = details;

                    for (var i = 0; i < details.results.length; i++) {
                        vm.submissionVisibility[details.results[i].id] = details.results[i].is_public;
                    }

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
                                    vm.currentPage = vm.submissionResult.count / 10;
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

            // long polling (5s) for leaderboard

            vm.start = function() {
                vm.stopFetchingSubmissions();
                vm.poller = $interval(function() {
                    var parameters = {};
                    parameters.url = "jobs/challenge/" + vm.challengeId + "/challenge_phase/" + vm.phaseId + "/submission/?page=" + Math.ceil(vm.currentPage);
                    parameters.method = 'GET';
                    parameters.data = {};
                    parameters.token = userKey;
                    parameters.callback = {
                        onSuccess: function(response) {
                            var details = response.data;

                            // Set the is_public flag corresponding to each submission
                            for (var i = 0; i < details.results.length; i++) {
                                vm.submissionVisibility[details.results[i].id] = details.results[i].is_public;
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
            var parameters = {};

            parameters.url = "jobs/challenge/" + vm.challengeId + "/challenge_phase/" + vm.phaseId + "/submission/?page=" + Math.ceil(vm.currentPage);
            parameters.method = 'GET';
            parameters.data = {};
            parameters.token = userKey;
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
        vm.refreshLeaderboard = function() {
            vm.startLoader("Loading Leaderboard Items");
            vm.leaderboard = {};
            var parameters = {};
            parameters.url = "jobs/" + "challenge_phase_split/" + vm.phaseSplitId + "/leaderboard/?page_size=1000";
            parameters.method = 'GET';
            parameters.data = {};
            parameters.token = userKey;
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

            var parameters = {};
            parameters.url = 'participants/participant_team';
            parameters.method = 'POST';
            parameters.data = {
                "team_name": vm.team.name
            };
            parameters.token = userKey;
            parameters.callback = {
                onSuccess: function() {
                    $rootScope.notify("success", "Team " + vm.team.name + " has been created successfully!");
                    vm.team.error = false;
                    vm.stopLoader();
                    vm.team.name = '';

                    vm.startLoader("Loading Teams");
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
            vm.phaseId = phaseId;

            // loader for loading submissions.
            vm.startLoader =  loaderService.startLoader;
            vm.startLoader("Loading Submissions");

            // get submissions of all the challenge phases
            vm.isNext = '';
            vm.isPrev = '';
            vm.currentPage = '';
            vm.showPagination = false;

            var parameters = {};
            parameters.url = "challenges/" + vm.challengeId + "/challenge_phase/" + vm.phaseId + "/submissions";
            parameters.method = 'GET';
            parameters.data = {};
            parameters.token = userKey;
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
                        vm.startLoader =  loaderService.startLoader;
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
                                    vm.currentPage = vm.submissionResult.count / 10;
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
            var parameters = {};
            parameters.url = "jobs/challenge/" + vm.challengeId + "/challenge_phase/" + vm.phaseId + "/submission/" + submission_id;
            parameters.method = 'PATCH';
            parameters.data = {
                "is_public": vm.submissionVisibility[submission_id]
            };
            parameters.token = userKey;
            parameters.callback = {
                onSuccess: function() {},
                onError: function() {}
            };

            utilities.sendRequest(parameters);
        };

        vm.showRemainingSubmissions = function() {
            var parameters = {};
            vm.remainingSubmissions = {};
            vm.remainingTime = {};
            vm.showClock = false;
            vm.showSubmissionNumbers = false;
            parameters.url = "jobs/"+ vm.challengeId + "/phases/"+ vm.phaseId + "/remaining_submissions";
            parameters.method = 'GET';
            parameters.token = userKey;
            parameters.callback = {
                onSuccess: function(response) {
                    var status = response.status;
                    var details = response.data;
                    if (status === 200) {
                        if (details.remaining_submissions_today_count > 0) {
                            vm.remainingSubmissions = details;
                            vm.showSubmissionNumbers = true;
                        } else {
                            vm.message = details;
                            vm.showClock = true;
                            vm.countDownTimer = function() {
                                vm.remainingTime = vm.message.remaining_time;
                                vm.days = Math.floor(vm.remainingTime/24/60/60);
                                vm.hoursLeft = Math.floor((vm.remainingTime) - (vm.days*86400));
                                vm.hours = Math.floor(vm.hoursLeft/3600);
                                vm.minutesLeft = Math.floor((vm.hoursLeft) - (vm.hours*3600));
                                vm.minutes = Math.floor(vm.minutesLeft/60);
                                vm.remainingSeconds = Math.floor(vm.remainingTime % 60);
                                if (vm.remainingSeconds < 10) {
                                    vm.remainingSeconds = "0" + vm.remainingSeconds;
                                }
                                if (vm.remainingTime === 0) {
                                    vm.showSubmissionNumbers = true;
                                }
                                else {
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
                onError: function() {
                    vm.stopLoader();
                    $rootScope.notify("error", "Some error occured. Please try again.");
                }
            };
            utilities.sendRequest(parameters);
        };

        vm.fileTypes = [{'name': 'csv'}];

        vm.downloadChallengeSubmissions = function() {
            if(vm.phaseId) {
                var parameters = {};
                parameters.url = "challenges/"+ vm.challengeId + "/phase/" + vm.phaseId + "/download_all_submissions/" + vm.fileSelected + "/";
                parameters.method = "GET";
                parameters.token = userKey;
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
        }else {
            $rootScope.notify("error", "Please select a challenge phase!");
        }
        };

        vm.showMdDialog = function(ev, submissionId) {
            for (var i=0;i<vm.submissionResult.count;i++){
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
            if(updateSubmissionMetaDataForm){
                var parameters = {};
                parameters.url = "jobs/challenge/" + vm.challengeId + "/challenge_phase/" + vm.phaseId + "/submission/" + vm.submissionId;
                parameters.method = 'PATCH';
                parameters.data = {
                    "method_name": vm.method_name,
                    "method_description": vm.method_description,
                    "project_url": vm.project_url,
                    "publication_url": vm.publication_url
                };
                parameters.token = userKey;
                parameters.callback = {
                    onSuccess: function(response) {
                        var status = response.status;
                        if (status === 200){
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
            }
            else{
              $mdDialog.hide();
            }
        };

        // Get the stars count and user specific starred or unstarred
        parameters = {};
        parameters.url = "challenges/"+ vm.challengeId + "/";
        parameters.method = 'GET';
        parameters.token = userKey;
        parameters.callback = {
            onSuccess: function(response) {
                var details = response.data;
                vm.count = details['count'] || 0;
                vm.is_starred = details['is_starred'];
                if (details['is_starred'] === false){
                    vm.data = 'Star';
                }
                else{
                    vm.data = 'Unstar';
                }
            },
            onError: function() {}
        };
        utilities.sendRequest(parameters);

        vm.starChallenge = function() {
            var parameters = {};
            parameters.url = "challenges/"+ vm.challengeId + "/";
            parameters.method = 'POST';
            parameters.data = {};
            parameters.token = userKey;
            parameters.callback = {
                onSuccess: function(response) {
                    var details = response.data;
                    vm.count = details['count'];
                    vm.is_starred = details['is_starred'];
                    if (details.is_starred === true) {
                        vm.data = 'Unstar';
                    } else{
                        vm.data = 'Star';
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
            if(editChallengeOverviewForm){
                var parameters = {};
                var challengeHostList = utilities.getData("challengeCreator");
                for (var challenge in challengeHostList) {
                    if (challenge==vm.challengeId) {
                            vm.challengeHostId = challengeHostList[challenge];
                            break;
                        }
                    }
                parameters.url = "challenges/challenge_host_team/" + vm.challengeHostId + "/challenge/" + vm.challengeId;
                parameters.method = 'PATCH';
                parameters.data = {
                    "description": vm.page.description

                };
                parameters.token = userKey;
                parameters.callback = {
                    onSuccess: function(response) {
                        var status = response.status;
                        if (status === 200){
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
            if(editSubmissionGuidelinesForm){
                var parameters = {};
                var challengeHostList = utilities.getData("challengeCreator");
                for (var challenge in challengeHostList) {
                    if (challenge==vm.challengeId) {
                            vm.challengeHostId = challengeHostList[challenge];
                            break;
                        }
                    }
                parameters.url = "challenges/challenge_host_team/" + vm.challengeHostId + "/challenge/" + vm.challengeId;
                parameters.method = 'PATCH';
                parameters.data = {
                    "submission_guidelines": vm.page.submission_guidelines

                };
                parameters.token = userKey;
                parameters.callback = {
                    onSuccess: function(response) {
                        var status = response.status;
                        if (status === 200){
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
            if(editEvaluationCriteriaForm){
                var parameters = {};
                var challengeHostList = utilities.getData("challengeCreator");
                for (var challenge in challengeHostList) {
                    if (challenge==vm.challengeId) {
                            vm.challengeHostId = challengeHostList[challenge];
                            break;
                        }
                    }
                parameters.url = "challenges/challenge_host_team/" + vm.challengeHostId + "/challenge/" + vm.challengeId;
                parameters.method = 'PATCH';
                parameters.data = {
                    "evaluation_details": vm.page.evaluation_details
                };
                parameters.token = userKey;
                parameters.callback = {
                    onSuccess: function(response) {
                        var status = response.status;
                        if (status === 200){
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
            $mdDialog.show({
                scope: $scope,
                preserveScope: true,
                targetEvent: ev,
                templateUrl: 'dist/views/web/challenge/edit-challenge/edit-challenge-evaluation-script.html',
                escapeToClose: false
            });
        };

        vm.editEvalScript = function(editEvaluationCriteriaForm) {
            if(editEvaluationCriteriaForm){
                var parameters = {};
                var formData = new FormData();
                formData.append("evaluation_script", vm.editEvaluationScript);
                var challengeHostList = utilities.getData("challengeCreator");
                for (var challenge in challengeHostList) {
                    if (challenge==vm.challengeId) {
                            vm.challengeHostId = challengeHostList[challenge];
                            break;
                        }
                    }
                parameters.url = "challenges/challenge_host_team/" + vm.challengeHostId + "/challenge/" + vm.challengeId;
                parameters.method = 'PATCH';
                parameters.data = formData;
                parameters.token = userKey;
                parameters.callback = {
                    onSuccess: function(response) {
                        var status = response.status;
                        if (status === 200){
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
            if(editTermsAndConditionsForm){
                var parameters = {};
                var challengeHostList = utilities.getData("challengeCreator");
                for (var challenge in challengeHostList) {
                    if (challenge==vm.challengeId) {
                            vm.challengeHostId = challengeHostList[challenge];
                            break;
                        }
                    }
                parameters.url = "challenges/challenge_host_team/" + vm.challengeHostId + "/challenge/" + vm.challengeId;
                parameters.method = 'PATCH';
                parameters.data = {
                    "terms_and_conditions": vm.page.terms_and_conditions
                };
                parameters.token = userKey;
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
            if(editChallengeTitleForm){
                var parameters = {};
                var challengeHostList = utilities.getData("challengeCreator");
                for (var challenge in challengeHostList) {
                    if (challenge==vm.challengeId) {
                            vm.challengeHostId = challengeHostList[challenge];
                            break;
                        }
                    }
                parameters.url = "challenges/challenge_host_team/" + vm.challengeHostId + "/challenge/" + vm.challengeId;
                parameters.method = 'PATCH';
                parameters.data = {
                    "title": vm.page.title
                };
                parameters.token = userKey;
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
            vm.phaseStartDate = new Date(phase.start_date);
            vm.phaseEndDate = new Date(phase.end_date);
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
            if(editChallengePhaseForm){
                vm.challengePhaseId = vm.page.challenge_phase.id;
                var parameters = {};
                parameters.url = "challenges/challenge/" + vm.challengeId + "/challenge_phase/" + vm.challengePhaseId;
                parameters.method = 'PATCH';
                var formData = new FormData();
                formData.append("name", vm.page.challenge_phase.name);
                formData.append("description", vm.page.challenge_phase.description);
                formData.append("start_date", vm.phaseStartDate.toISOString());
                formData.append("end_date", vm.phaseEndDate.toISOString());
                formData.append("max_submissions_per_day", vm.page.challenge_phase.max_submissions_per_day);
                formData.append("max_submissions", vm.page.challenge_phase.max_submissions);
                if (vm.testAnnotationFile){
                    formData.append("test_annotation", vm.testAnnotationFile);
                }
                parameters.data = formData;
                parameters.token = userKey;
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
                parameters = {};
                parameters.url = 'challenges/challenge/' + vm.challengeId + '/challenge_phase';
                parameters.method = 'GET';
                parameters.data = {};
                parameters.token = userKey;
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
    }

})();
