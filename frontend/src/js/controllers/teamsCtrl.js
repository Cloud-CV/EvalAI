// Invoking IIFE for teams
(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('TeamsCtrl', TeamsCtrl);

    TeamsCtrl.$inject = ['utilities', '$state', '$http'];

    function TeamsCtrl(utilities, $state, $http) {
        var vm = this;
        // console.log(vm.teamId)
        var userKey = utilities.getData('userKey');
        var challengePk = 1;

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
            onSuccess: function(response, status) {
                if (status == 200) {
                    vm.existTeam = response;

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
                        var parameters = {};
                        parameters.url = 'challenges/challenge/' + challengePk + '/participant_team/' + vm.teamId;
                        parameters.method = 'POST';
                        parameters.token = userKey;
                        parameters.callback = {
                            onSuccess: function(response, status) {
                                $state.go('web.challenge-page');
                            },
                            onError: function(error) {
                                vm.existTeamError = "Please select atleast one team";
                            }
                        };
                        utilities.sendRequest(parameters);
                    }

                    // to load data with pagination
                    vm.load = function(url) {

                        if (url != null) {

                            //store the header data in a variable 
                            var headers = {
                                'Authorization': "Token " + userKey
                            };

                            //Add headers with in your request
                            $http.get(url, { headers: headers }).success(function(response) {
                            	// reinitialized data
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
                            })
                        }
                    }
                }
            },
            onError: function(error) {
                vm.error = error;
                console.log(error);
                // navigate to permissions denied page
                $state.go('web.permission-denied');
            }
        };

        utilities.sendRequest(parameters);

        // function to create new team
        vm.createNewTeam = function() {
            var parameters = {};
            parameters.url = 'participants/participant_team';
            parameters.method = 'POST';
            parameters.data = {
                "team_name": vm.team.name
            }
            parameters.token = userKey;
            parameters.callback = {
                onSuccess: function(response, status) {
                    console.log(response)
                    vm.team.error = false;

                    // navigate to challenge page
                    $state.go('web.challenge-page');
                },
                onError: function(error) {
                    vm.team.error = error.team_name[0];
                }
            };

            utilities.sendRequest(parameters);
        }
    }

})();
