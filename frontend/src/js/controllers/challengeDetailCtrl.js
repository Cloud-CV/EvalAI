// Invoking IIFE for challenge page
(function() {

    'use strict';
    angular
        .module('evalai')
        .controller('ChallengeDetailCtrl', ChallengeDetailCtrl);

    ChallengeDetailCtrl.$inject = ['utilities', '$state', '$stateParams', '$rootScope'];

    function ChallengeDetailCtrl(utilities, $scope, $state, $stateParams, $rootScope) {
        var vm = this;
        $scope.challengeId = $stateParams.challengeId;
	}

})();
