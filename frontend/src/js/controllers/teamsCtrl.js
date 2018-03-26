// Invoking IIFE for teams
(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('TeamsCtrl', TeamsCtrl);

    TeamsCtrl.$inject = ['utilities','loaderService', '$scope', '$state', '$http', '$rootScope', '$mdDialog'];

    function TeamsCtrl(utilities,loaderService, $scope, $state, $http, $rootScope, $mdDialog) {
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
        vm.showPagination = false;

        // loader for existng teams// loader for exisiting teams
        vm.isExistLoader = false;
        vm.loaderTitle = '';
        vm.loaderContainer = angular.element('.exist-team-card');

        // show loader
        vm.startLoader = loaderService.startLoader;
        vm.stopLoader = loaderService.stopLoader;

        vm.activateCollapsible = function() {
            angular.element('.collapsible').collapsible();
        };

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

                    if (vm.existTeam.count === 0) {
                        vm.showPagination = false;
                        vm.paginationMsg = "No team exists for now, start by creating a new team!";
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


                    // select team from existing list
                    vm.selectExistTeam = function() {

                        // loader for exisiting teams
                        vm.isExistLoader = true;
                        vm.loaderTitle = '';
                        vm.loaderContainer = angular.element('.exist-team-card');


                        vm.startLoader("Loading Teams");
                        // loader end

                        var parameters = {};
                        parameters.url = 'challenges/challenge/' + challengePk + '/participant_team/' + vm.teamId;
                        parameters.method = 'POST';
                        parameters.token = userKey;
                        parameters.callback = {
                            onSuccess: function() {
                                $state.go('web.challenge-page.overview');
                                vm.stopLoader();
                            },
                            onError: function() {
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

        // function to create new team
        vm.createNewTeam = function() {
            vm.isExistLoader = true;
            vm.loaderTitle = '';
            vm.loaderContainer = angular.element('.new-team-card');

            // show loader

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

        vm.confirmDelete = function(ev, participantTeamId) {
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
                parameters.url = 'participants/remove_self_from_participant_team/' + participantTeamId;
                parameters.method = 'DELETE';
                parameters.data = {};
                parameters.token = userKey;
                parameters.callback = {
                    onSuccess: function() {

                        vm.team.error = false;
                        $rootScope.notify("info", "You have removed yourself successfully");

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
                    onError: function(response) {
                        var error = response.data['error'];
                        vm.stopLoader();
                        $rootScope.notify("error", error);
                    }
                };

                utilities.sendRequest(parameters);

            }, function() {
            });
        };


        vm.inviteOthers = function(ev, participantTeamId) {
            ev.stopPropagation();
            // Appending dialog to document.body to cover sidenav in docs app
            var confirm = $mdDialog.prompt()
                .title('Invite others to this team')
                .textContent('Enter the email address of the person')
                .placeholder('email')
                .ariaLabel('')
                .targetEvent(ev)
                .ok('Send Invite')
                .cancel('Cancel');

            $mdDialog.show(confirm).then(function(result) {
                var parameters = {};
                parameters.url = 'participants/participant_team/' + participantTeamId + '/invite';
                parameters.method = 'POST';
                parameters.data = {
                    "email": result
                };
                parameters.token = userKey;
                parameters.callback = {
                    onSuccess: function(response) {
                        var message = response.data['message'];
                        $rootScope.notify("success", message);
                    },
                    onError: function(response) {
                        var error = response.data['error'];
                        $rootScope.notify("error", error);
                    }
                };

                utilities.sendRequest(parameters);
            }, function() {
            });
        };


        vm.editTeamName = function(ev, participantTeamId) {
            ev.stopPropagation();
            // Edit the team name using UI.
            var confirm = $mdDialog.prompt()
                .title('Change Team Name')
                .textContent('Enter new team name')
                .placeholder('Team Name')
                .ariaLabel('')
                .targetEvent(ev)
                .ok('confirm')
                .cancel('Cancel');

            $mdDialog.show(confirm).then(function(result) {
                var parameters = {};
                parameters.url = 'participants/participant_team/' + participantTeamId;
                parameters.method = 'PATCH';
                parameters.data = {
                    "team_name": result,
                };
                parameters.token = userKey;
                parameters.callback = {
                    onSuccess: function() {
                        $rootScope.notify("success", "The Participant team name is successfully updated!");
                        var parameters = {};
                        // Retrives the updated lists and displays it.
                        parameters.url = 'participants/participant_team';
                        parameters.method = 'GET';
                        parameters.token = userKey;
                        parameters.callback = {
                            onSuccess: function(response) {
                                vm.existTeam.results = response.data.results;
                            },
                            onError: function() {
                                $rootScope.notify("error", "Team name cannot be changed!");
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
            }, function() {
            });
        };
    }

})();
