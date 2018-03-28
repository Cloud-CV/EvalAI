// Invoking IIFE for permission denied
(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('PermCtrl', PermCtrl);

    PermCtrl.$inject = ['utilities', '$rootScope'];

    function PermCtrl(utilities, $rootScope) {
        var vm = this;

        // message for not verified users
        vm.emailError = utilities.getData('emailError');
        vm.sendMail = false;
        // Function to request a new verification email.
        vm.requestLink = function () {
            var userKey = utilities.getData('userKey');
            var parameters = {};
            parameters.url = 'accounts/user/resend-email';
            parameters.method = 'POST';
            parameters.token = userKey;
            parameters.callback = {
                onSuccess: function() {
                    vm.sendMail = true;
                    $rootScope.notify("success", "The verification link was sent again.");
                },
                onError: function() {
                    vm.stopLoader();
                    $rootScope.notify("error", "Something went wrong, try again.");
                }
            };
            utilities.sendRequest(parameters);
        };
    }

})();
