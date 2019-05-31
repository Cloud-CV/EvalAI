// Invoking IIFE for create challenge using ui
(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('challengeCreateUsingUICtrl', challengeCreateUsingUICtrl);

        challengeCreateUsingUICtrl.$inject = ['utilities', '$state', '$rootScope'];

    function challengeCreateUsingUICtrl(utilities, $state, $rootScope) {
        var vm = this;
        vm.challengeTitle = '';
        vm.challengeStartDate = '';
        vm.challengeEndDate = '';
        vm.challengeEvaluationScript = null;

        vm.challengePhase = utilities.getData('challengePhase');
        vm.challengeSplit = utilities.getData('challengeSplit');
        vm.numberOfPhases = new Array(Integer.parseInt(vm.challengePhase));

        vm.submitChallengeDetails = function (challengeDetailsForm) {
            if (challengeDetailsForm) {
                $state.go('web.challenge-create-using-ui-step-2');
            }
        };
    };
})();