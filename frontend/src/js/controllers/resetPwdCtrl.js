// Invoking IIFE for teams
(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('ResetPwdCtrl', ResetPwdCtrl);

    ResetPwdCtrl.$inject = ['utilities', '$state', '$http', '$rootScope'];

    function ResetPwdCtrl(utilities, $state, $http, $rootScope) {
        var vm = this;
        vm.user = {};
        vm.wrnMsg = {};
        vm.isValid = {};        

        // function to change password
        vm.resetPassword = function() {
            var parameters = {};
            parameters.url = 'auth/password/reset/';
            parameters.method = 'POST';
            parameters.data = {
                "email": vm.user.email,
            }
            parameters.callback = {
                onSuccess: function(response, status) {
                    vm.user.error = false;
                    console.log("Password reset email sent to the user");
                    console.log(response);
                },
                onError: function(error, status) {
                    vm.user.error = "Failed";
                    if (status == 400) {
                        console.log("ERROR Occured");
                        console.log(error);
                        angular.forEach(error, function(value, key) {
                            if (key == 'email') {
                                vm.isValid.email = true;
                                vm.wrnMsg.email = value[0];
                            }
                        })
                    }
                }
            };

            utilities.sendRequest(parameters);
        }
    }

})();
