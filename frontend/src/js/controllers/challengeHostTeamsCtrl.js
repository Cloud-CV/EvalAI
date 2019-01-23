// Invoking IIFE for teams
(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('ChallengeHostTeamsCtrl', ChallengeHostTeamsCtrl);

    ChallengeHostTeamsCtrl.$inject = ['utilities', 'loaderService', '$scope', '$state', '$http', '$rootScope', '$mdDialog'];

    function ChallengeHostTeamsCtrl(utilities, loaderService, $scope, $state, $http, $rootScope, $mdDialog) {
        var vm = this;
        var userKey = utilities.getData('userKey');

        utilities.showLoader();

        // default variables/objects
        vm.team = {};
        vm.teamId = null;
        vm.existTeam = {};
        vm.currentPage = '';
        vm.isNext = '';
        vm.isPrev = '';
        vm.team.error = false;
        vm.showPagination = false;
        vm.hostTeamId = null;
        vm.challengeHostTeamId = null;

        // loader for existng teams// loader for exisiting teams
        vm.isExistLoader = false;
        vm.loaderTitle = '';
        vm.loaderContainer = angular.element('.exist-team-card');
         // show loader
        vm.startLoader = loaderService.startLoader;

        // stop loader
        vm.stopLoader = loaderService.stopLoader;

        vm.activateCollapsible = function() {
            angular.element('.collapsible').collapsible();
        };

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

                    if (vm.existTeam.count === 0) {
                        vm.showPagination = false;
                        vm.paginationMsg = "No team exists for now. Start by creating a new team!";
                    } else {
                        vm.activateCollapsible();
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
                        } else {
                            vm.stopLoader();
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


        vm.showMdDialog = function(ev, hostTeamId) {
            vm.hostTeamId = hostTeamId;
            parameters.url = 'hosts/challenge_host_team/' + hostTeamId;
            parameters.method = 'GET';
            parameters.token = userKey;
            parameters.callback = {
                onSuccess: function(response) {
                    vm.team.TeamName = response.data.team_name;
                    vm.team.TeamURL = response.data.team_url;
                },
                onError: function(response) {
                    var error = response.data['error'];
                    vm.stopLoader();
                    $rootScope.notify("error", error);
                }
            };
            utilities.sendRequest(parameters);

            $mdDialog.show({
                scope: $scope,
                preserveScope: true,
                targetEvent: ev,
                templateUrl: 'dist/views/web/edit-host-teams.html'
            });
        };


        vm.updateChallengeHostTeamData = function(updateChallengeHostTeamDataForm) {
            if (updateChallengeHostTeamDataForm) {
            var parameters = {};
            parameters.url = 'hosts/challenge_host_team/' + vm.hostTeamId;
            parameters.method = 'PATCH';
            parameters.data = {
                "team_name": vm.team.TeamName,
                "team_url": vm.team.TeamURL
            };
            parameters.token = userKey;
            parameters.callback = {
                onSuccess: function() {
                    $mdDialog.hide();
                    vm.team = {};
                    $rootScope.notify("success", "Host Team updated!");
                    var parameters = {};
                    // Retrives the updated lists and displays it.
                    parameters.url = 'hosts/challenge_host_team';
                    parameters.method = 'GET';
                    parameters.token = userKey;
                    parameters.callback = {
                        onSuccess: function(response) {
                            vm.existTeam.results = response.data.results;
                        },
                        onError: function(response) {
                            var error = response.data['error'];
                            vm.stopLoader();
                            $rootScope.notify("error", error);
                        }
                    };
                    utilities.sendRequest(parameters);
                },
                onError: function(response) {
                    var error;
                    if ('team_name' in response.data) {
                        error = response.data['team_name'];
                    }
                    else {
                        error = response.data['error'];
                    }
                    $rootScope.notify("error", error[0]);
                }
            };

            utilities.sendRequest(parameters);
            }
            else {
                $mdDialog.hide();
            }
        };


        // function to create new team
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
            parameters.url = 'hosts/create_challenge_host_team';
            parameters.method = 'POST';
            parameters.data = {
                "team_name": vm.team.name,
                "team_url": vm.team.url
            };
            parameters.token = userKey;
            parameters.callback = {
                onSuccess: function(response) {
                    $rootScope.notify("success", "New team- '" + vm.team.name + "' has been created");
                    var details = response.data;
                    vm.teamId = details.id;
                    vm.team.error = false;
                    vm.team = {};
                    vm.stopLoader();

                    vm.startLoader("Loading Teams");
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
                    $rootScope.notify("error",  error.team_name[0]);
                }
            };

            utilities.sendRequest(parameters);

        };

        vm.confirmDelete = function(ev, hostTeamId) {
            ev.stopPropagation();
            // Appending dialog to document.body to cover sidenav in docs app
            var confirm = $mdDialog.confirm()
                .title('Would you like to remove yourself?')
                .textContent('Note: This action will remove you from the team.')
                .ariaLabel('Lucky day')
                .targetEvent(ev)
                .ok('Yes')
                .cancel("No");

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

        vm.inviteOthers = function(ev, hostTeamId) {
            ev.stopPropagation();
            // Appending dialog to document.body 
            var confirm = $mdDialog.prompt()
                .title('Add other memebers to this Team')
                .textContent('Enter the email address of the person')
                .placeholder('email')
                .ariaLabel('')
                .targetEvent(ev)
                .ok('Add')
                .cancel('Cancel');

            $mdDialog.show(confirm).then(function(result) {

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

    vm.storeChallengeHostTeamId = function() {

        utilities.storeData('challengeHostTeamId', vm.challengeHostTeamId);
        $state.go('web.challenge-create');
    };

    }

})();
