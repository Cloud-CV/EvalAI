// Invoking IIFE for permission denied
(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('PermCtrl', PermCtrl);

    PermCtrl.$inject = ['utilities'];

    function PermCtrl(utilities) {
        var vm = this;

        // message for not verified users
        vm.emailError = utilities.getData('emailError');
    }

})();
