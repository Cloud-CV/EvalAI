// Invoking IIFE
(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('MainCtrl', MainCtrl);

    MainCtrl.$inject = ['utilities', '$rootScope', '$state'];

    function MainCtrl(utilities, $rootScope, $state) {

        var vm = this;
        vm.user = {};
        vm.challengeList = [];
        vm.isChallenge = true;
        vm.isMore = false;
        // store the next redirect value
        vm.redirectUrl = {};


        vm.getChallenge = function() {
            // get featured challenge (unauthorized)
            var parameters = {};
            parameters.url = 'challenges/featured/';
            parameters.method = 'GET';
            parameters.token = null;
            parameters.callback = {
                onSuccess: function(response) {
                    vm.challengeList = response.data;
                },
                onError: function() {}
            };
            utilities.sendRequest(parameters);
        };


        vm.init = function() {
            // Check if token is available in localstorage
            var userKey = utilities.getData('userKey');
            // check for authenticated user
            if (userKey) {
                var parameters = {};
                parameters.url = 'auth/user/';
                parameters.method = 'GET';
                parameters.token = userKey;
                parameters.callback = {
                    onSuccess: function(response) {
                        var status = response.status;
                        var details = response.data;
                        if (status == 200) {
                            vm.user.name = details.username;
                        }
                    },
                    onError: function(response) {
                        var status = response.status;
                        if (status == 401) {
                            utilities.resetStorage();
                            $state.go("auth.login");
                            $rootScope.isAuth = false;
                        }
                    }
                };
                utilities.sendRequest(parameters);
            }
        };


        vm.hostChallenge = function() {
            if ($rootScope.isAuth === true) {
                $state.go('web.challenge-host-teams');
            } else {
                $state.go('auth.login');
                $rootScope.previousState = "web.challenge-host-teams";
            }
        };


        vm.profileDropdown = function() {
            angular.element(".dropdown-button").dropdown();
        };


        vm.init();
        vm.getChallenge();
        angular.element('.carousel').carousel({
            duration: 200
            // dist: 0,
            // indicators: true
        });
    }
})();
