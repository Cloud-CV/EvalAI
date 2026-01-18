// Invoking IIFE for dashboard
(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('DashCtrl', DashCtrl);

    DashCtrl.$inject = ['utilities', '$state', '$rootScope'];

    function DashCtrl(utilities, $state, $rootScope) {
        var vm = this;

        // User has verified email or not
        vm.isPrivileged = true;

        vm.challengeCount = 0;
        vm.hostTeamCount = 0;
        vm.hostTeamExist = false;
        vm.participatedTeamCount = 0;
        // get token
        var userKey = utilities.getData('userKey');

        utilities.showLoader();

        // store the next redirect value
        vm.redirectUrl = {};

        var parameters = {};
        parameters.url = 'auth/user/';
        parameters.method = 'GET';
        parameters.token = userKey;
        parameters.callback = {
            onSuccess: function(response) {
                var status = response.status;
                var details = response.data;
                if (status == 200) {
                    vm.name = details.username;
                }
            },
            onError: function(response) {
                utilities.hideLoader();
                var status = response.status;
                var error = response.data;
                if (status == 403) {
                    vm.error = error;
                    utilities.storeData('emailError', error.detail);
                    vm.isPrivileged = false;
                } else if (status == 401) {
                    alert("Timeout, Please login again to continue!");
                    utilities.resetStorage();
                    $state.go("auth.login");
                    $rootScope.isAuth = false;

                }
            }
        };
        utilities.sendRequest(parameters);

        vm.getAllChallenges = function(parameters, counter){
            parameters.callback = {
                onSuccess: function(response) {
                    var status = response.status;
                    var details = response.data;
                    if (status == 200) {
                        vm[counter] += details.results.length;
                        if (details.next !== null){
                            var url = details.next;
                            var slicedUrl = url.substring(url.indexOf('challenges/challenge'), url.length);
                            parameters.url = slicedUrl;
                            vm.getAllChallenges(parameters, counter);
                        }
                    }
                    if (vm.hostTeamCount == 0) {
                        vm.hostTeamExist = false;
                    } else {
                        vm.hostTeamExist = true;
                    }
                },
                onError: function(response) {
                    utilities.hideLoader();
                    var status = response.status;
                    var error = response.data;
                    if (status == 403) {
                        vm.error = error;
                        vm.isPrivileged = false;
                    } else if (status == 401) {
                        alert("Timeout, Please login again to continue!");
                        utilities.resetStorage();
                        $state.go("auth.login");
                        $rootScope.isAuth = false;

                    }
                }
            };

            utilities.sendRequest(parameters);
        };

        // get all ongoing challenges.
        parameters.url = 'challenges/challenge/present/approved/public';
        parameters.method = 'GET';
        parameters.token = userKey;
        vm.getAllChallenges(parameters, "challengeCount");

        //check for host teams.
        parameters.url = 'hosts/challenge_host_team/';
        parameters.method = 'GET';
        parameters.token = userKey;
        parameters.callback = {
            onSuccess: function(response) {
                var status = response.status;
                var details = response.data;
                if (status == 200) {
                    vm.hostTeamCount = details.results.length;
                }
            },
            onError: function(response) {
                utilities.hideLoader();
                var status = response.status;
                var error = response.data;
                if (status == 403) {
                    vm.error = error;
                    vm.isPrivileged = false;
                } else if (status == 401) {
                    alert("Timeout, Please login again to continue!");
                    utilities.resetStorage();
                    $state.go("auth.login");
                    $rootScope.isAuth = false;

                }
            }
        };

        utilities.sendRequest(parameters);

        //check for participated teams.
        parameters.url = 'participants/participant_team';
        parameters.method = 'GET';
        parameters.token = userKey;
        parameters.callback = {
            onSuccess: function(response) {
                var status = response.status;
                var details = response.data;
                if (status == 200) {
                    vm.participatedTeamCount = details.results.length;
                }
                utilities.hideLoader();
            },
            onError: function(response) {
                utilities.hideLoader();
                var status = response.status;
                var error = response.data;
                if (status == 403) {
                    vm.error = error;
                    vm.isPrivileged = false;
                } else if (status == 401) {
                    alert("Timeout, Please login again to continue!");
                    utilities.resetStorage();
                    $state.go("auth.login");
                    $rootScope.isAuth = false;

                }
            }
        };

        utilities.sendRequest(parameters);

        vm.hostChallenge = function() {
            $state.go('web.challenge-host-teams');
        };
    }

})();
