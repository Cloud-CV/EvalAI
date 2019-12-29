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
        vm.sendMail = false;
        
        vm.requestLink = function() {
            var userKey = utilities.getData('userKey');
            var parameters = {};
            
            parameters.url = 'accounts/user/resend-email';
            parameters.method = 'POST';
            parameters.token = userKey;
            
            utilities.sendRequest(parameters);
            
    }

})();
