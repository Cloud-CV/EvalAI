// Invoking IIFE
(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('MainCtrl', MainCtrl);

    MainCtrl.$inject = ['utilities', '$rootScope', '$state', '$mdDialog'];

    function MainCtrl(utilities, $rootScope, $state, $mdDialog) {

        var vm = this;

        vm.user = {};
        vm.challengeList = {};
        vm.challengeCount = 0;
        vm.isMore = false;

        // get token
        var userKey = utilities.getData('userKey');

        // getting challenge (unauthorized)
        var parameters = {};

        parameters.url = 'challenges/challenge/present';
        parameters.method = 'GET';

        parameters.token = null;
        parameters.callback = {
            onSuccess: function(response) {
                var details = response.data;
                vm.challengeList = details;
                if (vm.challengeList.count > 10) {
                    vm.challengeCount = '10+';
                } else {
                    vm.challengeCount = vm.challengeList.count;
                }

                if (vm.challengeList.results[0].description.length > 120) {
                    vm.isMore = true;
                } else {
                    vm.isMore = false;
                }
            },
            onError: function() {
            }
        };

        utilities.sendRequest(parameters);

        // check for authenticated user
        if (userKey) {
            parameters = {};
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
        vm.hostChallenge = function() {

            var alert = $mdDialog.alert()
                .title('Host a challenge')
                .textContent('Thanks for your interest in hosting a Challenge on EvalAI. We will release this feature soon!')
                .ok('Close');

            $mdDialog.show(alert);
        };

        vm.profileDropdown = function() {
            angular.element(".dropdown-button").dropdown();

        };
    }


})();
