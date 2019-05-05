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
        vm.isFormError = false;

        // default parameters
        $rootScope.canShowOldPassword = false;
        $rootScope.canShowNewPassword = false;
        $rootScope.canShowNewConfirmPassword = false;

        vm.changepassContainer = angular.element('.change-passowrd-card');

        vm.startLoader = function(msg) {
            $rootScope.isLoader = true;
            $rootScope.loaderTitle = msg;
            vm.changepassContainer.addClass('low-screen');
        };

        // stop loader
        vm.stopLoader = function() {
            $rootScope.isLoader = false;
            $rootScope.loaderTitle = '';
            vm.changepassContainer.removeClass('low-screen');
        };

        // toggle old password visibility
        vm.toggleOldPasswordVisibility = function() {
            $rootScope.canShowOldPassword = !$rootScope.canShowOldPassword;
        };

        // toggle new password visibility
        vm.toggleNewPasswordVisibility = function() {
            $rootScope.canShowNewPassword = !$rootScope.canShowNewPassword;
        };

        // toggle new password again visibility
        vm.toggleNewConfirmVisibility = function() {
            $rootScope.canShowNewConfirmPassword = !$rootScope.canShowNewConfirmPassword;
        };

        // function to change password
        vm.changePassword = function(resetconfirmFormValid) {
          if(resetconfirmFormValid){


            vm.startLoader("Changing Your Password");
            var parameters = {};
            parameters.url = 'auth/password/change/';
            parameters.method = 'POST';
            parameters.data = {
                "old_password": vm.user.old_password,
                "new_password1": vm.user.new_password1,
                "new_password2": vm.user.new_password2,
                "uid": $state.params.user_id,
            };
            parameters.token = userKey;
                parameters.callback = {
                    onSuccess: function() {
                        vm.user.error = false;
                        $rootScope.notify("success", "Your password has been changed successfully!");
                        vm.stopLoader();
                        // navigate to challenge page
                        // $state.go('web.challenge-page.overview');
                    },
                    onError: function(response) {
                        vm.user.error = "Failed";
                        vm.isFormError = true;
                        var oldpassword_valid ,password1_valid, password2_valid;
                        try {
                            oldpassword_valid = typeof(response.data.old_password) !== 'undefined' ? true : false;
                            password1_valid = typeof(response.data.new_password1) !== 'undefined' ? true : false;
                            password2_valid = typeof(response.data.new_password2) !== 'undefined' ? true : false;
                            if (oldpassword_valid) {
                                vm.FormError = Object.values(response.data.old_password).join(" ");
                            }else if (password1_valid) {
                                vm.FormError = Object.values(response.data.new_password1).join(" ");
                            } else if (password2_valid) {
                                vm.FormError = Object.values(response.data.new_password2).join(" ");
                            }
                        } catch (error) { 
                            vm.FormError = "Something went wrong! Please refresh the page and try again.";
                        }
                        vm.stopLoader();
                    }
                };

                utilities.sendRequest(parameters);

            }else {
              vm.stopLoader();
            }
        };
    }

})();
