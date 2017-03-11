// Invoking IIFE for permission denied
(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('PermCtrl', PermCtrl);

    PermCtrl.$inject = ['utilities', '$state'];

    function PermCtrl(utilities, $state, $stateParams) {
        var vm = this;

        // message for not verified users
        vm.emailError = utilities.getData('emailError');
    }

})();
