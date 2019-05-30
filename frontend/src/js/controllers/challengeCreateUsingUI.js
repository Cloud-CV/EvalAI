// Invoking IIFE for create challenge using ui
(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('ChallengeCreateUsingUICtrl', ChallengeCreateUsingUICtrl);

    ChallengeCreateUsingUICtrl.$inject = ['utilities', '$state', '$rootScope'];

    function ChallengeCreateUsingUICtrl(utilities, $state, $rootScope) {
        var vm = this;
        vm.challengePhase = utilities.getData('challengePhase');
        vm.challengeSplit = utilities.getData('challengeSplit');
        console.log('asdasd', vm.challengePhase);
    };
});