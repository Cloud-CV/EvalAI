// Invoking IIFE for teams
(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('ChangePwdCtrl', ChangePwdCtrl);

    ChangePwdCtrl.$inject = ['utilities', '$state', '$http', '$rootScope'];

    function ChangePwdCtrl(utilities, $state, $http, $rootScope) {
        var vm = this;
        var userKey = utilities.getData('userKey');

        // function to change password
        vm.changePassword = function() {
            vm.loginContainer = angular.element('.change-passowrd-card');

            var parameters = {};
            parameters.url = 'auth/password/change/';
            parameters.method = 'POST';
            parameters.data = {
                "old_password": vm.user.old_password,
                "new_password1": vm.user.new_password1,
                "new_password2": vm.user.new_password2,
            }
            parameters.token = userKey;
            parameters.callback = {
                onSuccess: function(response, status) {
                    vm.user.error = false;
                    console.log("PASSWORD CHANGED SUCCESSFULLY");
                    console.log(response);
                    // navigate to challenge page
                    // $state.go('web.challenge-page.overview');
                },
                onError: function(error) {
                    console.log("ERROR Occured");
                    console.log(error);
                    vm.user.error = "Failed";
                }
            };

            utilities.sendRequest(parameters);
        }
    }

})();
