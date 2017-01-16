// Invoking IIFE for challenge page
(function() {

    'use strict';
    angular
        .module('evalai')
        .controller('ChallengeCtrl', ChallengeCtrl);

    ChallengeCtrl.$inject = ['utilities', '$scope', '$state', '$stateParams', '$rootScope'];

    function ChallengeCtrl(utilities, $scope, $state, $stateParams, $rootScope) {
        var vm = this;
        $scope.challengeId = $stateParams.challengeId;
        vm.wrnMsg = {};
        vm.page = {};

        vm.phases = {};
        vm.isValid = {};
        var userKey = utilities.getData('userKey');

        utilities.showLoader();

        // get details of the particular challenge
        var parameters = {};
        parameters.url = 'challenges/challenge/' + $scope.challengeId + '/';
        parameters.method = 'GET';
        parameters.data = {}
        parameters.token = userKey;
        parameters.callback = {
            onSuccess: function(response) {
                var status = response.status;
                var response = response.data;
                console.log(response);
                vm.page = response;
                // navigate to challenge page
                // $state.go('web.challenge-page.overview');
                utilities.hideLoader();
            },
            onError: function(response) {
                var status = response.status;
                var error = response.data;
                utilities.hideLoader();
            }
        };

        utilities.sendRequest(parameters);

        // get details of the particular challenge
        var parameters = {};
        parameters.url = 'challenges/challenge/' + $scope.challengeId + '/challenge_phase';
        parameters.method = 'GET';
        parameters.data = {}
        parameters.token = userKey;
        parameters.callback = {
            onSuccess: function(response) {
                var status = response.status;
                var response = response.data;
                console.log(response);
                vm.phases = response;
                // navigate to challenge page
                // $state.go('web.challenge-page.overview');
                utilities.hideLoader();
            },
            onError: function(response) {
                var status = response.status;
                var error = response.data;
                console.log(error);
                utilities.hideLoader();
            }
        };

        utilities.sendRequest(parameters);


    }
})();
