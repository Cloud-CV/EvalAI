// Invoking IIFE for teams
(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('TeamsCtrl', TeamsCtrl);

    TeamsCtrl.$inject = ['utilities', '$state', '$http', '$rootScope'];

    function TeamsCtrl(utilities, $state, $http, $rootScope) {
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
                        parameters.url = 'challenges/challenge/' + challengePk + '/participant_team/' + vm.teamId;
                        parameters.method = 'POST';
                        parameters.token = userKey;
                        parameters.callback = {
                            onSuccess: function(response) {
                                var status = response.status;
                                var response = response.data;
                                $state.go('web.challenge-page.overview');
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
            parameters.url = 'participants/participant_team';
            parameters.method = 'POST';
            parameters.data = {
                "team_name": vm.team.name
            }
            parameters.token = userKey;
            parameters.callback = {
                onSuccess: function(response) {
                    var status = response.status;
                    var response = response.data;
                    vm.team.error = false;

                    // navigate to challenge page
                    $state.go('web.challenge-page.overview');
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
        }
    }

})();
