// Invoking IIFE for challenge page
(function() {

    'use strict';
    angular
        .module('evalai')
        .controller('ChallengeCtrl', ChallengeCtrl);

    ChallengeCtrl.$inject = ['utilities', '$scope', '$state', '$stateParams', '$rootScope'];

    function ChallengeCtrl(utilities, $scope, $state, $stateParams, $rootScope) {
        var vm = this;
        vm.challengeId = $stateParams.challengeId;
        vm.wrnMsg = {};
        vm.page = {};
        vm.isParticipated = false;
        var flag = 0;
        vm.phases = {};
        vm.isValid = {};
        var userKey = utilities.getData('userKey');

        utilities.showLoader();

        // get details of the particular challenge
        var parameters = {};
        parameters.url = 'challenges/challenge/' + vm.challengeId + '/';
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
                alert("");
                utilities.storeData('emailError', error.detail);
                $state.go('web.permission-denied');
                utilities.hideLoader();
            }
        };

        utilities.sendRequest(parameters);

        // get details of the particular challenge
        var parameters = {};
        parameters.url = 'challenges/challenge/' + vm.challengeId + '/challenge_phase';
        parameters.method = 'GET';
        parameters.data = {}
        parameters.token = userKey;
        parameters.callback = {
            onSuccess: function(response) {
                var status = response.status;
                var response = response.data;
                vm.phases = response;
                // navigate to challenge page
                // $state.go('web.challenge-page.overview');
                utilities.hideLoader();
            },
            onError: function(response) {
                var status = response.status;
                var error = response.data;
                utilities.storeData('emailError', error.detail);
                $state.go('web.permission-denied');
                utilities.hideLoader();
            }
        };

        utilities.sendRequest(parameters);


        // get details of the particular challenge
        var parameters = {};
        parameters.url = 'participants/participant_teams/challenges/user';
        parameters.method = 'GET';
        parameters.data = {}
        parameters.token = userKey;
        parameters.callback = {
            onSuccess: function(response) {
                var status = response.status;
                var response = response.data;

                for (var i in response.challenge_participant_team_list) {
                    console.log
                    if (response.challenge_participant_team_list[i].challenge != null && response.challenge_participant_team_list[i].challenge.id == vm.challengeId) {
                        flag = 1;
                        break;
                    }

                }

                if (flag == 1) {
                    vm.isParticipated = false
                } else {
                    vm.isParticipated = true;
                }
                // vm.phases = response;
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

    }
})();
