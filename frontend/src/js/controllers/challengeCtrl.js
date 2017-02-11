// Invoking IIFE for challenge page
(function() {

    'use strict';
    angular
        .module('evalai')
        .controller('ChallengeCtrl', ChallengeCtrl);

    ChallengeCtrl.$inject = ['utilities', '$scope', '$state', '$http', '$stateParams', '$rootScope', 'Upload'];

    function ChallengeCtrl(utilities, $scope, $state, $http, $stateParams, $rootScope, Upload) {
        var vm = this;
        vm.challengeId = $stateParams.challengeId;
        vm.phaseId = null;
        vm.input_file = null;
        vm.wrnMsg = {};
        vm.page = {};
        vm.isParticipated = false;
        vm.isActive = false;
        var flag = 0;
        vm.phases = {};
        vm.isValid = {};
        var userKey = utilities.getData('userKey');

        vm.subErrors = {};

        utilities.showLoader();

        // get details of the particular challenge
        var parameters = {};
        parameters.url = 'challenges/challenge/' + vm.challengeId + '/';
        parameters.method = 'GET';
        parameters.data = {}
        parameters.token = userKey;
        parameters.callback = {
            onSuccess: function(response) {
                var status = response.status;
                var response = response.data;
                vm.page = response;
                vm.isActive = response.is_active;

                if(vm.page.image == null){
                	vm.page.image = "dist/images/logo.png";
                }

                if (vm.isActive == true) {

                    // get details of challenges corresponding to participant teams of that user
                    var parameters = {};
                    parameters.url = 'participants/participant_teams/challenges/user';
                    parameters.method = 'GET';
                    parameters.data = {}
                    parameters.token = userKey;
                    parameters.callback = {
                        onSuccess: function(response) {
                            var status = response.status;
                            var response = response.data;

                            for (var i in response.challenge_participant_team_list) {
                                if (response.challenge_participant_team_list[i].challenge != null && response.challenge_participant_team_list[i].challenge.id == vm.challengeId) {
                                    vm.isParticipated = true;
                                    break;
                                }
                            }

                            if (vm.isParticipated == false) {

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
                                        var response = response.data;
                                        if (status == 200) {
                                            vm.existTeam = response;

                                            // clear error msg from storage
                                            utilities.deleteData('emailError');

                                            // condition for pagination
                                            if (vm.existTeam.next == null) {
                                                vm.isNext = 'disabled';
                                            } else {
                                                vm.isNext = '';
                                            }

                                            if (vm.existTeam.previous == null) {
                                                vm.isPrev = 'disabled';
                                            } else {
                                                vm.isPrev = '';
                                            }
                                            if (vm.existTeam.next != null) {
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
                                                }

                                                // stop loader
                                                vm.stopLoader = function() {
                                                    vm.isExistLoader = false;
                                                    vm.loaderTitle = '';
                                                    vm.loginContainer.removeClass('low-screen');
                                                }

                                                vm.startLoader("Loading Teams");
                                                // loader end

                                                var parameters = {};
                                                parameters.url = 'challenges/challenge/' + vm.challengeId + '/participant_team/' + vm.teamId;
                                                parameters.method = 'POST';
                                                parameters.token = userKey;
                                                parameters.callback = {
                                                    onSuccess: function(response) {
                                                        var status = response.status;
                                                        var response = response.data;
                                                        vm.isParticipated = true;
                                                        $state.go('web.challenge-main.challenge-page.submission');
                                                        vm.stopLoader();
                                                    },
                                                    onError: function(response) {
                                                        var status = response.status;
                                                        var error = response.data;
                                                        vm.existTeamError = "Please select a team";
                                                        vm.stopLoader();
                                                    }
                                                };
                                                utilities.sendRequest(parameters);
                                            }

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
                                                }

                                                // stop loader
                                                vm.stopLoader = function() {
                                                    vm.isExistLoader = false;
                                                    vm.loaderTitle = '';
                                                    vm.loginContainer.removeClass('low-screen');
                                                }

                                                vm.startLoader("Loading Teams");
                                                if (url != null) {

                                                    //store the header data in a variable
                                                    var headers = {
                                                        'Authorization': "Token " + userKey
                                                    };

                                                    //Add headers with in your request
                                                    $http.get(url, { headers: headers }).then(function(response) {
                                                        // reinitialized data
                                                        var status = response.status;
                                                        var response = response.data;
                                                        vm.existTeam = response;

                                                        // condition for pagination
                                                        if (vm.existTeam.next == null) {
                                                            vm.isNext = 'disabled';
                                                            vm.currentPage = vm.existTeam.count / 10;
                                                        } else {
                                                            vm.isNext = '';
                                                            vm.currentPage = parseInt(vm.existTeam.next.split('page=')[1] - 1);
                                                        }

                                                        if (vm.existTeam.previous == null) {
                                                            vm.isPrev = 'disabled';
                                                        } else {
                                                            vm.isPrev = '';
                                                        }
                                                        vm.stopLoader();
                                                    })
                                                }
                                            }

                                        }
                                        utilities.hideLoader();
                                    },
                                    onError: function(response) {
                                        var status = response.status;
                                        var error = response.data;
                                        utilities.storeData('emailError', error.detail);
                                        $state.go('web.permission-denied');
                                        utilities.hideLoader();
                                    }
                                };

                                utilities.sendRequest(parameters);

                            }
                            // This condition means that the user is eligible to make submissions
                            else if (vm.isParticipated == true) {
                                vm.makeSubmission = function() {

                                    var fileVal = angular.element(".file-path").val();

                                    if (fileVal == null || fileVal == "") {
                                        vm.subErrors.msg = "Please upload file!"
                                    } else {
                                        vm.isExistLoader = true;
                                        vm.loaderTitle = '';
                                        vm.loginContainer = angular.element('.exist-team-card');

                                        // show loader
                                        vm.startLoader = function(msg) {
                                            vm.isExistLoader = true;
                                            vm.loaderTitle = msg;
                                            vm.loginContainer.addClass('low-screen');
                                        }

                                        // stop loader
                                        vm.stopLoader = function() {
                                            vm.isExistLoader = false;
                                            vm.loaderTitle = '';
                                            vm.loginContainer.removeClass('low-screen');
                                        }

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
                                                var status = response.status;
                                                var response = response.data;
                                                // vm.input_file.name = '';

                                                angular.forEach(
                                                    angular.element("input[type='file']"),
                                                    function(inputElem) {
                                                        angular.element(inputElem).val(null);
                                                    }
                                                );

                                                angular.element(".file-path").val(null);


                                                vm.phaseId = null;
                                                vm.subErrors.msg = "Your submission has been recorded succesfully!"
                                                vm.stopLoader();
                                            },
                                            onError: function(response) {
                                                var status = response.status;
                                                var error = response.data;

                                                vm.phaseId = null;
                                                if (status == 404) {

                                                    vm.subErrors.msg = "Please select phase!"
                                                } else if (status == 400) {
                                                    vm.subErrors.msg = error.input_file[0]
                                                } else {
                                                    vm.subErrors.msg = error.error
                                                }
                                                vm.stopLoader();
                                            }
                                        };

                                        utilities.sendRequest(parameters, 'header', 'upload');
                                    }
                                }
                            }
                            utilities.hideLoader();
                        },
                        onError: function(response) {
                            var status = response.status;
                            var error = response.data;
                            utilities.hideLoader();
                        }
                    };

                    utilities.sendRequest(parameters);
                }

                utilities.hideLoader();

            },
            onError: function(response) {
                var status = response.status;
                var error = response.data;
                utilities.storeData('emailError', error.detail);
                $state.go('web.permission-denied');
                utilities.hideLoader();
            }
        };

        utilities.sendRequest(parameters);

        // get details of the particular challenge phase
        var parameters = {};
        parameters.url = 'challenges/challenge/' + vm.challengeId + '/challenge_phase';
        parameters.method = 'GET';
        parameters.data = {}
        parameters.token = userKey;
        parameters.callback = {
            onSuccess: function(response) {
                var status = response.status;
                var response = response.data;
                vm.phases = response;
                // navigate to challenge page
                // $state.go('web.challenge-page.overview');
                utilities.hideLoader();
            },
            onError: function(response) {
                var status = response.status;
                var error = response.data;
                utilities.storeData('emailError', error.detail);
                $state.go('web.permission-denied');
                utilities.hideLoader();
            }
        };

        utilities.sendRequest(parameters);

        // my submissions
        vm.isResult = false;
        vm.getResults = function(phaseId) {
            vm.isResult = true;
            // loader for exisiting teams
            vm.isExistLoader = true;
            vm.loaderTitle = '';
            vm.loginContainer = angular.element('.exist-team-card');

            // show loader
            vm.startLoader = function(msg) {
                vm.isExistLoader = true;
                vm.loaderTitle = msg;
                vm.loginContainer.addClass('low-screen');
            }

            // stop loader
            vm.stopLoader = function() {
                vm.isExistLoader = false;
                vm.loaderTitle = '';
                vm.loginContainer.removeClass('low-screen');
            }

            vm.startLoader("Loading Teams");

            // get details of the particular challenge phase
            vm.isNext = '';
            vm.isPrev = '';
            vm.currentPage = '';

            var parameters = {};
            parameters.url = "jobs/challenge/" + vm.challengeId + "/challenge_phase/" + phaseId + "/submission/";
            parameters.method = 'GET';
            parameters.data = {}
            parameters.token = userKey;
            parameters.callback = {
                onSuccess: function(response) {
                    var status = response.status;
                    var response = response.data;
                    vm.submissionResult = response;
                    // navigate to challenge page
                    // $state.go('web.challenge-page.overview');
                    if (vm.submissionResult.next == null) {
                        vm.isNext = 'disabled';
                    } else {
                        vm.isNext = '';

                    }
                    if (vm.submissionResult.previous == null) {
                        vm.isPrev = 'disabled';
                    } else {
                        vm.isPrev = '';
                    }
                    if (vm.submissionResult.next != null) {
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
                        }

                        // stop loader
                        vm.stopLoader = function() {
                            vm.isExistLoader = false;
                            vm.loaderTitle = '';
                            vm.loginContainer.removeClass('low-screen');
                        }

                        vm.startLoader("Loading Teams");
                        if (url != null) {

                            //store the header data in a variable
                            var headers = {
                                'Authorization': "Token " + userKey
                            };

                            //Add headers with in your request
                            $http.get(url, { headers: headers }).then(function(response) {
                                // reinitialized data
                                var status = response.status;
                                var response = response.data;
                                vm.submissionResult = response;

                                // condition for pagination
                                if (vm.submissionResult.next == null) {
                                    vm.isNext = 'disabled';
                                    vm.currentPage = vm.submissionResult.count / 3;
                                } else {
                                    vm.isNext = '';
                                    vm.currentPage = parseInt(vm.submissionResult.next.split('page=')[1] - 1);
                                }

                                if (vm.submissionResult.previous == null) {
                                    vm.isPrev = 'disabled';
                                } else {
                                    vm.isPrev = '';
                                }
                                vm.stopLoader();
                            })
                        } else {
                            vm.stopLoader();
                        }


                    }

                },
                onError: function(response) {
                    var status = response.status;
                    var error = response.data;
                    utilities.storeData('emailError', error.detail);
                    $state.go('web.permission-denied');
                    vm.stopLoader();
                }
            };

            utilities.sendRequest(parameters);

            // Show leaderboard
            vm.leaderboard = {};
            var parameters = {};
            parameters.url = "jobs/challenge/" + vm.challengeId + "/challenge_phase/" + phaseId + "/leaderboard/";
            parameters.method = 'GET';
            parameters.data = {}
            parameters.token = userKey;
            parameters.callback = {
                onSuccess: function(response) {
                    var status = response.status;
                    var response = response.data;
                    vm.leaderboard = response.results;

                    $scope.sortType     = 'overall_acc'; // set the default sort type
                    $scope.sortReverse  = true;  // set the default sort order

                    vm.stopLoader();
                },
                onError: function(response) {
                    var status = response.status;
                    var error = response.data;
                    vm.leaderboard.error = error;
                    vm.stopLoader();
                }
            };

            utilities.sendRequest(parameters);
        }
    }

})();
