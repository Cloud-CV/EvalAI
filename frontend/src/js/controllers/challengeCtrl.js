// Invoking IIFE for challenge page
(function() {

    'use strict';
    angular
        .module('evalai')
        .controller('ChallengeCtrl', ChallengeCtrl);

    ChallengeCtrl.$inject = ['utilities', '$state', '$stateParams', '$rootScope'];

    function ChallengeCtrl(utilities, $state, $stateParams, $rootScope) {
        var vm = this;

        // utilities.showLoader();
    }

})();
