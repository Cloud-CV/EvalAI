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
        vm.wrnMsg = {};
        vm.isValid = {};
        vm.user = {};
        // function to change password
        vm.changePassword = function(resetconfirmFormValid) {
          if(resetconfirmFormValid){
            vm.loginContainer = angular.element('.change-passowrd-card');
            vm.startLoader("Changing Your Password");
            var parameters = {};
            parameters.url = 'auth/password/change/';
            parameters.method = 'POST';
            parameters.data = {
                "old_password": vm.user.old_password,
                "new_password1": vm.user.new_password1,
                "new_password2": vm.user.new_password2,
                "uid": $state.params.user_id,
                "token": $state.params.reset_token,
            }
                parameters.callback = {
                    onSuccess: function(response) {
                        var status = response.status;
                        var response = response.data;
                        vm.user.error = false;
                        console.log("PASSWORD CHANGED SUCCESSFULLY");
                        console.log(response);
                        vm.stopLoader();
                        // navigate to challenge page
                        // $state.go('web.challenge-page.overview');
                    },
                    onError: function(response) {
                        var status = response.status;
                        var error = response.data;
                        vm.user.error = "Failed";
                        var token_valid, oldpassword_valid ,password1_valid, password2_valid;
                        try {
                            token_valid = typeof(response.data.token) !== 'undefined' ? true : false;
                            oldpassword_valid = typeof(response.data.old_password) !== 'undefined' ? true : false;
                            password1_valid = typeof(response.data.new_password1) !== 'undefined' ? true : false;
                            password2_valid = typeof(response.data.new_password2) !== 'undefined' ? true : false;
                            if (token_valid) {
                                vm.FormError = "this link has been already used or expired.";
                            }else if (oldpassword_valid) {
                                vm.FormError = response.data.oldpassword_valid[0] + " " + response.data.oldpassword_valid[1];
                            }else if (password1_valid) {
                                vm.FormError = response.data.new_password1[0] + " " + response.data.new_password1[1];
                            } else if (password2_valid) {
                                vm.FormError = response.data.new_password2[0] + " " + response.data.new_password2[1];
                            } else {
                                console.log("Unhandled Error");
                            }
                        } catch (error) {
                            vm.FormError = "Something went wrong! Please refresh the page and try again.";
                        }
                        vm.stopLoader();
                    }
                };

                utilities.sendRequest(parameters);

            }else {
              console.log("Form fields are not valid !");
              vm.stopLoader();
            }
        }
    }

})();
