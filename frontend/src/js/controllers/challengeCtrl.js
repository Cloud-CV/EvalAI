// Invoking IIFE for challenge page
(function() {

    'use strict';
    angular
        .module('evalai')
        .controller('ChallengeCtrl', ChallengeCtrl);

    ChallengeCtrl.$inject = ['utilities', '$scope', '$state', '$http', '$stateParams', '$rootScope'];

    function ChallengeCtrl(utilities, $scope, $state, $http, $stateParams, $rootScope) {
        var vm = this;
        vm.challengeId = $stateParams.challengeId;
        vm.wrnMsg = {};
        vm.page = {};
        vm.isParticipated = false;
        vm.isActive = false;
        var flag = 0;
        vm.phases = {};
        vm.isValid = {};
        var userKey = utilities.getData('userKey');

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
                console.log(response.is_active);
                vm.isActive = response.is_active;
                if (vm.isActive == true){

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

                            if (vm.isParticipated == false){

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
                                            if (response.next != null) {
                                                vm.currentPage = response.next.split('page=')[1] - 1;
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
                                                            vm.currentPage = response.count / 10;
                                                        } else {
                                                            vm.isNext = '';
                                                            vm.currentPage = parseInt(response.next.split('page=')[1] - 1);
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

    }
})();
