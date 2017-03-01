// Invoking IIFE for challenge page
(function() {

    'use strict';
    angular
        .module('evalai')
        .controller('ChallengeCtrl', ChallengeCtrl);

    ChallengeCtrl.$inject = ['utilities', '$scope', '$state', '$http', '$stateParams', '$rootScope', 'Upload', '$interval'];

    function ChallengeCtrl(utilities, $scope, $state, $http, $stateParams, $rootScope, Upload, $interval) {
        var vm = this;
        vm.challengeId = $stateParams.challengeId;
        vm.phaseId = null;
        vm.phaseSplitId = null;
        vm.input_file = null;
        vm.wrnMsg = {};
        vm.page = {};
        vm.isParticipated = false;
        vm.isActive = false;
        var flag = 0;
        vm.phases = {};
        vm.phaseSplits = {};
        vm.isValid = {};
        vm.showUpdate = false;
        vm.showLeaderboardUpdate = false;
        vm.poller = null;
        vm.stopLeaderboard = function() {};
        vm.stopFetchingSubmissions = function() {};

        // loader for existing teams
        vm.isExistLoader = false;
        vm.loaderTitle = '';
        vm.loginContainer = angular.element('.exist-team-card');

        // show loader
        vm.startExistLoader = function(msg) {
            vm.isExistLoader = true;
            vm.loaderTitle = msg;
            vm.loginContainer.addClass('low-screen');
        };

        // stop loader
        vm.stopExistLoader = function() {
            vm.isExistLoader = false;
            vm.loaderTitle = '';
            vm.loginContainer.removeClass('low-screen');
        };

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
                var status = response.status;
                var details = response.data;
                vm.page = details;
                vm.isActive = details.is_active;


                if (vm.page.image === null) {
                    vm.page.image = "dist/images/logo.png";

                }

                if (vm.isActive) {

                    // get details of challenges corresponding to participant teams of that user
                    var parameters = {};
                    parameters.url = 'participants/participant_teams/challenges/user';
                    parameters.method = 'GET';
                    parameters.data = {};
                    parameters.token = userKey;
                    parameters.callback = {
                        onSuccess: function(response) {
                            var status = response.status;
                            var details = response.data;

                            for (var i in details.challenge_participant_team_list) {
                                if (details.challenge_participant_team_list[i].challenge !== null && details.challenge_participant_team_list[i].challenge.id == vm.challengeId) {
                                    vm.isParticipated = true;
                                    break;
                                }
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
                                                vm.loginContainer = angular.element('.exist-team-card');

                                                // show loader
                                                vm.startLoader = function(msg) {
                                                    vm.isExistLoader = true;
                                                    vm.loaderTitle = msg;
                                                    vm.loginContainer.addClass('low-screen');
                                                };

                                                // stop loader
                                                vm.stopLoader = function() {
                                                    vm.isExistLoader = false;
                                                    vm.loaderTitle = '';
                                                    vm.loginContainer.removeClass('low-screen');
                                                };

                                                vm.startLoader("Loading Teams");
                                                // loader end

                                                var parameters = {};
                                                parameters.url = 'challenges/challenge/' + vm.challengeId + '/participant_team/' + vm.teamId;
                                                parameters.method = 'POST';
                                                parameters.token = userKey;
                                                parameters.callback = {
                                                    onSuccess: function(response) {
                                                        var details = response.data;
                                                        vm.isParticipated = true;
                                                        $state.go('web.challenge-main.challenge-page.submission');
                                                        vm.stopLoader();
                                                    },
                                                    onError: function(response) {
                                                        var error = response.data;
                                                        vm.existTeamError = "Please select a team";
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
                                                vm.loginContainer = angular.element('.exist-team-card');

                                                // show loader
                                                vm.startLoader = function(msg) {
                                                    vm.isExistLoader = true;
                                                    vm.loaderTitle = msg;
                                                    vm.loginContainer.addClass('low-screen');
                                                };

                                                // stop loader
                                                vm.stopLoader = function() {
                                                    vm.isExistLoader = false;
                                                    vm.loaderTitle = '';
                                                    vm.loginContainer.removeClass('low-screen');
                                                };

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
                            else if (vm.isParticipated) {
                                vm.makeSubmission = function() {

                                    var fileVal = angular.element(".file-path").val();

                                    if (fileVal === null || fileVal === "") {
                                        vm.subErrors.msg = "Please upload file!";
                                    } else {
                                        vm.isExistLoader = true;
                                        vm.loaderTitle = '';
                                        vm.loginContainer = angular.element('.exist-team-card');

                                        // show loader
                                        vm.startLoader = function(msg) {
                                            vm.isExistLoader = true;
                                            vm.loaderTitle = msg;
                                            vm.loginContainer.addClass('low-screen');
                                        };

                                        // stop loader
                                        vm.stopLoader = function() {
                                            vm.isExistLoader = false;
                                            vm.loaderTitle = '';
                                            vm.loginContainer.removeClass('low-screen');
                                        };

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

                                        parameters.data = formData;

                                        parameters.token = userKey;
                                        parameters.callback = {
                                            onSuccess: function(response) {
                                                // vm.input_file.name = '';

                                                angular.forEach(
                                                    angular.element("input[type='file']"),
                                                    function(inputElem) {
                                                        angular.element(inputElem).val(null);
                                                    }
                                                );

                                                angular.element(".file-path").val(null);


                                                vm.phaseId = null;
                                                // vm.subErrors.msg = "Your submission has been recorded succesfully!";
                                                $rootScope.notify("success", "Your submission has been recorded succesfully!");

                                                vm.stopLoader();
                                            },
                                            onError: function(response) {
                                                var status = response.status;
                                                var error = response.data;

                                                vm.phaseId = null;
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
                                };
                            }
                            utilities.hideLoader();
                        },
                        onError: function(response) {
                            var error = response.data;
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
            vm.loginContainer = angular.element('.exist-team-card');

            // show loader
            vm.startLoader = function(msg) {
                vm.isExistLoader = true;
                vm.loaderTitle = msg;
                vm.loginContainer.addClass('low-screen');
            };

            // stop loader
            vm.stopLoader = function() {
                vm.isExistLoader = false;
                vm.loaderTitle = '';
                vm.loginContainer.removeClass('low-screen');
            };

            vm.startLoader("Loading Leaderboard Items");


            // Show leaderboard
            vm.leaderboard = {};
            var parameters = {};
            parameters.url = "jobs/" + "challenge_phase_split/" + vm.phaseSplitId + "/leaderboard/";
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
                    parameters.url = "jobs/" + "challenge_phase_split/" + vm.phaseSplitId + "/leaderboard/";
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
            // loader for exisiting teams
            vm.isExistLoader = true;
            vm.loaderTitle = '';
            vm.loginContainer = angular.element('.exist-team-card');

            // show loader
            vm.startLoader = function(msg) {
                vm.isExistLoader = true;
                vm.loaderTitle = msg;
                vm.loginContainer.addClass('low-screen');
            };

            // stop loader
            vm.stopLoader = function() {
                vm.isExistLoader = false;
                vm.loaderTitle = '';
                vm.loginContainer.removeClass('low-screen');
            };

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
                        vm.loginContainer = angular.element('.exist-team-card');

                        // show loader
                        vm.startLoader = function(msg) {
                            vm.isExistLoader = true;
                            vm.loaderTitle = msg;
                            vm.loginContainer.addClass('low-screen');
                        };

                        // stop loader
                        vm.stopLoader = function() {
                            vm.isExistLoader = false;
                            vm.loaderTitle = '';
                            vm.loginContainer.removeClass('low-screen');
                        };

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
                    parameters.url = "jobs/challenge/" + vm.challengeId + "/challenge_phase/" + vm.phaseId + "/submission/";
                    parameters.method = 'GET';
                    parameters.data = {};
                    parameters.token = userKey;
                    parameters.callback = {
                        onSuccess: function(response) {
                            var status = response.status;
                            var details = response.data;
                            if (vm.submissionResult.results.count !== details.results.count) {
                                vm.showUpdate = true;
                            } else {
                                for (var i = 0; i < details.results.length; i++) {
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
            vm.startLoader("Loading Submissions");
            vm.submissionResult = {};
            var parameters = {};

            parameters.url = "jobs/challenge/" + vm.challengeId + "/challenge_phase/" + vm.phaseId + "/submission/";
            parameters.method = 'GET';
            parameters.data = {};
            parameters.token = userKey;
            parameters.callback = {
                onSuccess: function(response) {
                    var details = response.data;
                    vm.submissionResult = details;
                    vm.showUpdate = false;
                    vm.stopLoader();
                },
                onError: function(response) {
                    vm.stopLoader();
                }
            };

            utilities.sendRequest(parameters);
        };
        vm.refreshLeaderboard = function() {
            vm.startLoader("Loading Leaderboard Items");
            vm.leaderboard = {};
            var parameters = {};
            parameters.url = "jobs/" + "challenge_phase_split/" + vm.phaseSplitId + "/leaderboard/";
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

            // show loader
            vm.startLoader = function(msg) {
                vm.isLoader = true;
                vm.loaderTitle = msg;
                vm.newContainer.addClass('low-screen');
            };

            // stop loader
            vm.stopLoader = function() {
                vm.isLoader = false;
                vm.loaderTitle = '';
                vm.newContainer.removeClass('low-screen');
            };

            vm.startLoader("Loading Teams");

            var parameters = {};
            parameters.url = 'participants/participant_team';
            parameters.method = 'POST';
            parameters.data = {
                "team_name": vm.team.name
            };
            parameters.token = userKey;
            parameters.callback = {
                onSuccess: function(response) {
                    $rootScope.notify("success", "Team- " + vm.team.name + " has been created successfully!");
                    var details = response.data;
                    vm.team.error = false;
                    vm.stopLoader();
                    vm.team.name = '';

                    vm.startExistLoader("Loading Teams");
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


                                vm.stopExistLoader();
                            }
                        },
                        onError: function(response) {
                            vm.stopExistLoader();
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
