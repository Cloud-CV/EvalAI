(function () {

    'use strict';

    angular
        .module('evalai')
        .controller('DashCtrl', DashCtrl);

    DashCtrl.$inject = ['utilities', '$state', '$rootScope'];

    function DashCtrl(utilities, $state, $rootScope) {
        var vm = this;

        vm.isPrivileged = true;

        vm.challengeCount = null;
        vm.hostTeamCount = null;
        vm.hostTeamExist = false;
        vm.participatedTeamCount = null;

        vm.challengeCountLoading = true;
        vm.hostTeamCountLoading = true;
        vm.participatedTeamCountLoading = true;

        var userKey = utilities.getData('userKey');

        utilities.showLoader();

        vm.redirectUrl = {};

        var userParams = {
            url: 'auth/user/',
            method: 'GET',
            token: userKey,
            callback: {
                onSuccess: function (response) {
                    var status = response.status;
                    var details = response.data;
                    if (status == 200) {
                        vm.name = details.username;
                    }
                },
                onError: function (response) {
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
            }
        };
        utilities.sendRequest(userParams);

        vm.getAllChallenges = function (params, counter) {
            var requestParams = {
                url: params.url,
                method: params.method,
                token: params.token,
                callback: {
                    onSuccess: function (response) {
                        var status = response.status;
                        var details = response.data;
                        if (status == 200) {
                            if (vm[counter] === null) {
                                vm[counter] = 0;
                            }
                            vm[counter] += details.results.length;
                            if (details.next !== null) {
                                var url = details.next;
                                var slicedUrl = url.substring(url.indexOf('challenges/challenge'), url.length);
                                var nextParams = {
                                    url: slicedUrl,
                                    method: 'GET',
                                    token: params.token
                                };
                                vm.getAllChallenges(nextParams, counter);
                            } else {
                                if (counter === "challengeCount") {
                                    vm.challengeCountLoading = false;
                                }
                            }
                        }
                    },
                    onError: function (response) {
                        utilities.hideLoader();
                        if (counter === "challengeCount") {
                            vm.challengeCountLoading = false;
                        }
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
                }
            };
            utilities.sendRequest(requestParams);
        };

        var challengeParams = {
            url: 'challenges/challenge/present/approved/public',
            method: 'GET',
            token: userKey
        };
        vm.getAllChallenges(challengeParams, "challengeCount");

        var hostTeamParams = {
            url: 'hosts/challenge_host_team/',
            method: 'GET',
            token: userKey,
            callback: {
                onSuccess: function (response) {
                    var status = response.status;
                    var details = response.data;
                    if (status == 200) {
                        vm.hostTeamCount = details.results.length;
                        vm.hostTeamCountLoading = false;
                        if (vm.hostTeamCount == 0) {
                            vm.hostTeamExist = false;
                        } else {
                            vm.hostTeamExist = true;
                        }
                    }
                },
                onError: function (response) {
                    utilities.hideLoader();
                    vm.hostTeamCountLoading = false;
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
            }
        };
        utilities.sendRequest(hostTeamParams);

        var participantTeamParams = {
            url: 'participants/participant_team',
            method: 'GET',
            token: userKey,
            callback: {
                onSuccess: function (response) {
                    var status = response.status;
                    var details = response.data;
                    if (status == 200) {
                        vm.participatedTeamCount = details.results.length;
                        vm.participatedTeamCountLoading = false;
                    }
                    utilities.hideLoader();
                },
                onError: function (response) {
                    utilities.hideLoader();
                    vm.participatedTeamCountLoading = false;
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
            }
        };
        utilities.sendRequest(participantTeamParams);

        vm.hostChallenge = function () {
            $state.go('web.challenge-host-teams');
        };
    }

})();
