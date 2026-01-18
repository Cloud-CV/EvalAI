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

        // Track pending requests to hide loader when all complete
        var pendingRequests = 4;
        var checkAllComplete = function() {
            pendingRequests--;
            if (pendingRequests === 0) {
                utilities.hideLoader();
            }
        };

        // Helper for common error handling
        var handleError = function(response) {
            checkAllComplete();
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
        };

        // Get user info
        var userParams = {
            url: 'auth/user/',
            method: 'GET',
            token: userKey,
            callback: {
                onSuccess: function(response) {
                    if (response.status == 200) {
                        vm.name = response.data.username;
                    }
                    checkAllComplete();
                },
                onError: function(response) {
                    checkAllComplete();
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
            }
        };

        // Get ongoing challenges count - use API's count field instead of paginating
        var challengeParams = {
            url: 'challenges/challenge/present/approved/public',
            method: 'GET',
            token: userKey,
            callback: {
                onSuccess: function(response) {
                    if (response.status == 200) {
                        // Use count from API response instead of paginating through all results
                        vm.challengeCount = response.data.count || response.data.results.length;
                    }
                    checkAllComplete();
                },
                onError: handleError
            }
        };

        // Get host teams count - use API's count field
        var hostTeamParams = {
            url: 'hosts/challenge_host_team/',
            method: 'GET',
            token: userKey,
            callback: {
                onSuccess: function(response) {
                    if (response.status == 200) {
                        vm.hostTeamCount = response.data.count || response.data.results.length;
                        vm.hostTeamExist = vm.hostTeamCount > 0;
                    }
                    checkAllComplete();
                },
                onError: handleError
            }
        };

        // Get participated teams count - use API's count field
        var participantParams = {
            url: 'participants/participant_team',
            method: 'GET',
            token: userKey,
            callback: {
                onSuccess: function(response) {
                    if (response.status == 200) {
                        vm.participatedTeamCount = response.data.count || response.data.results.length;
                    }
                    checkAllComplete();
                },
                onError: handleError
            }
        };

        // Fire all requests in parallel
        utilities.sendRequest(userParams);
        utilities.sendRequest(challengeParams);
        utilities.sendRequest(hostTeamParams);
        utilities.sendRequest(participantParams);

        vm.hostChallenge = function() {
            $state.go('web.challenge-host-teams');
        };
    }

})();
