// Invoking IIFE for teams
(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('ChallengeHostTeamsCtrl', ChallengeHostTeamsCtrl);

    ChallengeHostTeamsCtrl.$inject = ['utilities', '$state', '$http', '$rootScope', '$mdDialog'];

    function ChallengeHostTeamsCtrl(utilities, $state, $http, $rootScope, $mdDialog) {
        var vm = this;
        // console.log(vm.teamId)
        var userKey = utilities.getData('userKey');
        var challengePk = 1;

        utilities.showLoader();

        // default variables/objects
        vm.team = {};
        vm.teamId = null;
        vm.existTeam = {};
        vm.currentPage = '';
        vm.isNext = '';
        vm.isPrev = '';
        vm.team.error = false;

        var parameters = {};
        parameters.url = 'hosts/challenge_host_team/';
        parameters.method = 'GET';
        parameters.token = userKey;
        parameters.callback = {
            onSuccess: function(response) {
                var status = response.status;
                var response = response.data;
                if (status == 200) {
                    vm.existTeam = response;
                    console.log(response);

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

        // function to create new team
        vm.createNewTeam = function() {
            vm.isLoader = true;
            vm.loaderTitle = '';
            vm.loginContainer = angular.element('.new-team-card');

            // show loader
            vm.startLoader = function(msg) {
                vm.isLoader = true;
                vm.loaderTitle = msg;
                vm.loginContainer.addClass('low-screen');
            }

            // stop loader
            vm.stopLoader = function() {
                vm.isLoader = false;
                vm.loaderTitle = '';
                vm.loginContainer.removeClass('low-screen');
            }

            vm.startLoader("Loading Teams");

            var parameters = {};
            parameters.url = 'hosts/create_challenge_host_team';
            parameters.method = 'POST';
            parameters.data = {
                "team_name": vm.team.name
            }
            parameters.token = userKey;
            parameters.callback = {
                onSuccess: function(response) {
                    var status = response.status;
                    var response = response.data;
                    vm.teamId = response.id;
                    vm.team.error = false;

                    var parameters = {};
                    parameters.url = 'hosts/challenge_host_team/';
                    parameters.method = 'GET';
                    parameters.token = userKey;
                    parameters.callback = {
                        onSuccess: function(response) {
                            var status = response.status;
                            var response = response.data;
                            if (status == 200) {
                                vm.existTeam = response;
                            }
                        }
                    };
                    utilities.sendRequest(parameters);
                    vm.stopLoader();
                },
                onError: function(response) {
                    var status = response.status;
                    var error = response.data;
                    vm.stopLoader();
                    vm.team.error = error.team_name[0];
                }
            };

            utilities.sendRequest(parameters);
            vm.reset = function() {
                 vm.team.name = '';
                 };
            vm.reset();
        }
        
        vm.inviteOthers = function(ev, hostTeamId) {
            // Appending dialog to document.body 
            var confirm = $mdDialog.prompt()
                .title('Invite others to this Team')
                .textContent('Enter the email address of the person')
                .placeholder('email')
                .ariaLabel('')
                .targetEvent(ev)
                .ok('Send Invite')
                .cancel('Cancel');

                $mdDialog.show(confirm).then(function(result) {
                    var parameters = {};
                    parameters.url = 'hosts/challenge_host_teams/' + hostTeamId + '/invite';
                    parameters.method = 'POST';
                    parameters.data = {
                        "email": result
                    }
                    parameters.token = userKey;
                    parameters.callback = {
                        onSuccess: function(response) {
                            var status = response.status;
                            var response = response.data;
                        },
                        onError: function(response) {
                            var status = response.status;
                            var error = response.data;
                        }
                    };

                    utilities.sendRequest(parameters);
                });
        };
        
    }

})();
