// Invoking IIFE for dashboard
(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('AnalyticsCtrl', DashCtrl);

    DashCtrl.$inject = ['utilities', '$state', '$rootScope'];

    function DashCtrl(utilities, $state, $rootScope) {
        var vm = this;

        vm.hostTeam = {};
        vm.teamId = null;
        vm.currentTeamName = null;
        vm.challengeListCount = 0;
        vm.challengeList = {};
        vm.challengeAnalysisDetail = {};
        vm.isTeamSelected = false;
        vm.challengeId = null;
        vm.currentChallengeDetails = {};
        vm.currentPhase = [];
        vm.totalSubmission = [];
        // vm.challengeCount = 0;
        // vm.hostTeamCount = 0;
        // vm.hostTeamExist = false;
        // vm.participatedTeamCount = 0;
        // // get token

        // if (vm.teamId == null) {
        //     vm.isTeamSelected = false;
        // } else {
        //     vm.isTeamSelected = true;
        // }
        var userKey = utilities.getData('userKey');

        var parameters = {};
        parameters.url = 'hosts/challenge_host_team/';
        parameters.method = 'GET';
        parameters.token = userKey;
        parameters.callback = {
            onSuccess: function(response) {
                var status = response.status;
                var details = response.data;
                if (status == 200) {
                    vm.hostTeam = details.results;

                }
            },
            onError: function(response) {
                var status = response.status;
                var error = response.data;
                if (status == 403) {
                    vm.error = error;

                    // navigate to permissions denied page
                    $state.go('web.permission-denied');
                } else if (status == 401) {
                    alert("Timeout, Please login again to continue!");
                    utilities.resetStorage();
                    $state.go("auth.login");
                    $rootScope.isAuth = false;

                }
            }
        };
        utilities.sendRequest(parameters);


        parameters.url = 'challenges/challenge?mode=host';
        parameters.method = 'GET';
        parameters.token = userKey;
        parameters.callback = {
            onSuccess: function(response) {
                var status = response.status;
                var details = response.data;
                if (status == 200) {
                    vm.challengeList = details.results;
                    vm.challengeListCount = details.count;
                }
            },
            onError: function(response) {
                var status = response.status;
                var error = response.data;
                if (status == 403) {
                    vm.error = error;

                    // navigate to permissions denied page
                    $state.go('web.permission-denied');
                } else if (status == 401) {
                    alert("Timeout, Please login again to continue!");
                    utilities.resetStorage();
                    $state.go("auth.login");
                    $rootScope.isAuth = false;

                }
            }
        };
        utilities.sendRequest(parameters);

        vm.showChallengeAnalysis = function() {
            if (vm.challengeId != null) {
                parameters.url = 'challenges/challenge/' + vm.challengeId + '/challenge_phase';
                parameters.method = 'GET';
                parameters.token = userKey;
                parameters.callback = {
                    onSuccess: function(response) {
                        var status = response.status;
                        var details = response.data;


                        if (status === 200) {
                            vm.currentPhase = details.results;

                            for (var phaseCount = 0; phaseCount < vm.currentPhase.length; phaseCount++) {
                                parameters.url = 'analytics/challenge_phase/' + vm.currentPhase[phaseCount].id + '/submission';
                                parameters.method = 'GET';
                                parameters.token = userKey;
                                parameters.callback = {
                                    onSuccess: function(response) {
                                        var status = response.status;
                                        var details = response.data;
                                        if (status == 200) {
                                            vm.totalSubmission[phaseCount] = details.submission_total;
                                        }
                                    },
                                    onError: function(response) {
                                        var status = response.status;
                                        var error = response.data;
                                        if (status == 403) {
                                            vm.error = error;

                                            // navigate to permissions denied page
                                            $state.go('web.permission-denied');
                                        } else if (status == 401) {
                                            alert("Timeout, Please login again to continue!");
                                            utilities.resetStorage();
                                            $state.go("auth.login");
                                            $rootScope.isAuth = false;

                                        }
                                    }
                                };
                                utilities.sendRequest(parameters);
                            }

                        }
                    },
                    onError: function(response) {
                        var status = response.status;
                        var error = response.data;
                        if (status == 403) {
                            vm.error = error;

                            // navigate to permissions denied page
                            $state.go('web.permission-denied');
                        } else if (status == 401) {
                            alert("Timeout, Please login again to continue!");
                            utilities.resetStorage();
                            $state.go("auth.login");
                            $rootScope.isAuth = false;

                        }
                    }
                };

                utilities.sendRequest(parameters);
                vm.isTeamSelected = true;
                for (var i = 0; i < vm.challengeList.length; i++) {

                    if (vm.challengeList[i].id == vm.challengeId) {
                        vm.currentChallengeDetails = vm.challengeList[i];
                    }
                }
                console.log(vm.currentChallengeDetails);
            } else {
                vm.isTeamSelected = false;
            }
        };

        // // get all ongoing challenges.
        // parameters.url = 'challenges/challenge/present';
        // parameters.method = 'GET';
        // parameters.token = userKey;
        // parameters.callback = {
        //     onSuccess: function(response) {
        //         var status = response.status;
        //         var details = response.data;
        //         if (status == 200) {
        //             vm.challengeCount = details.count;
        //             if(vm.hostTeamCount == 0){
        //                 vm.hostTeamExist = false;
        //             }
        //             else{
        //                 vm.hostTeamExist = true;
        //             }
        //         }
        //     },
        //     onError: function(response) {
        //         var status = response.status;
        //         var error = response.data;
        //         if (status == 403) {
        //             vm.error = error;

        //             // navigate to permissions denied page
        //             $state.go('web.permission-denied');
        //         } else if (status == 401) {
        //             alert("Timeout, Please login again to continue!");
        //             utilities.resetStorage();
        //             $state.go("auth.login");
        //             $rootScope.isAuth = false;

        //         }
        //     }
        // };

        // utilities.sendRequest(parameters);

        //  //check for host teams.
        // parameters.url = 'hosts/challenge_host_team';
        // parameters.method = 'GET';
        // parameters.token = userKey;
        // parameters.callback = {
        //     onSuccess: function(response) {
        //         var status = response.status;
        //         var details = response.data;
        //         if (status == 200) {
        //             vm.hostTeamCount = details.count;
        //         }
        //     },
        //     onError: function(response) {
        //         var status = response.status;
        //         var error = response.data;
        //         if (status == 403) {
        //             vm.error = error;

        //             // navigate to permissions denied page
        //             $state.go('web.permission-denied');
        //         } else if (status == 401) {
        //             alert("Timeout, Please login again to continue!");
        //             utilities.resetStorage();
        //             $state.go("auth.login");
        //             $rootScope.isAuth = false;

        //         }
        //     }
        // };

        // utilities.sendRequest(parameters);

        // //check for participated teams.
        // parameters.url = 'participants/participant_team';
        // parameters.method = 'GET';
        // parameters.token = userKey;
        // parameters.callback = {
        //     onSuccess: function(response) {
        //         var status = response.status;
        //         var details = response.data;
        //         if (status == 200) {
        //             vm.participatedTeamCount = details.count;
        //         }
        //     },
        //     onError: function(response) {
        //         var status = response.status;
        //         var error = response.data;
        //         if (status == 403) {
        //             vm.error = error;

        //             // navigate to permissions denied page
        //             $state.go('web.permission-denied');
        //         } else if (status == 401) {
        //             alert("Timeout, Please login again to continue!");
        //             utilities.resetStorage();
        //             $state.go("auth.login");
        //             $rootScope.isAuth = false;

        //         }
        //     }
        // };

        // utilities.sendRequest(parameters);

        // vm.hostChallenge = function() {

        //     var alert = $mdDialog.alert()
        //         .title('Host a challenge')
        //         .htmlContent('Please send an email to <a href="mailto:admin@cloudcv.org" class="blue-text">admin@cloudcv.org</a> with the details of the challenge and we will get back soon.')
        //         .ok('Close');

        //     $mdDialog.show(alert);
        // };
    }

})();
