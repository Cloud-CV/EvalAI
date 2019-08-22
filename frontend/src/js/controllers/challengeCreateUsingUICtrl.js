// Invoking IIFE for create challenge using ui
(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('challengeCreateUsingUICtrl', challengeCreateUsingUICtrl);

    challengeCreateUsingUICtrl.$inject = ['utilities', '$state', '$rootScope'];

    function challengeCreateUsingUICtrl(utilities, $state, $rootScope) {
        var vm = this;
        var userKey = utilities.getData('userKey');
        vm.hostTeamId = utilities.getData('challengeHostTeamId');
        vm.challengeTitle = '';
        vm.challengeStartDate = '';
        vm.challengeEndDate = '';
        vm.challengeLogo = null;
        vm.challengeEvaluationScript = null;
        vm.challengePhase = utilities.getData('challengePhase');
        vm.challengeSplit = utilities.getData('challengeSplit');
        // vm.numberOfPhases = new Array(Integer.parseInt(vm.challengePhase));

        vm.createChallengeUsingUI = function (challengeDetailsForm) {
            if (challengeDetailsForm) {
                var parameters = {};
                parameters.url = 'challenges/challenge_host_team/' + vm.hostTeamId + '/challenge';
                parameters.method = 'POST';
                console.log(vm.challengeLogo, vm.challengeEvaluationScript);
                // var formData = new FormData();
                // formData.append("title", vm.challengeTitle);
                // formData.append("start_date", vm.challengeStartDate);
                // formData.append("end_date", vm.challengeEndDate);
                // formData.append("image", vm.challengeLogo);
                // formData.append("evaluation_script", vm.challengeEvaluationScript);
                parameters.data = {
                    "title": vm.challengeTitle,
                    "start_date": vm.challengeStartDate,
                    "end_date": vm.challengeEndDate,
                    "is_registration_open": true,
                };
                parameters.token = userKey;
                parameters.callback = {
                    onSuccess: function(response) {
                        console.log(response)
                        $state.go("home");
                    },
                    onError: function(response) {
                        console.log("error", response);
                    }
                };
                utilities.sendRequest(parameters);
            }
        };
    };
})();