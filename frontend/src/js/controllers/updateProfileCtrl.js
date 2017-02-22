// Invoking IIFE for teams
/* jshint shadow:true */
(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('UpdateProfileCtrl', UpdateProfileCtrl);

    UpdateProfileCtrl.$inject = ['utilities', '$state', '$http', '$rootScope'];

    function UpdateProfileCtrl(utilities, $state, $http, $rootScope) {
        var vm = this;
        var userKey = utilities.getData('userKey');
        vm.wrnMsg = {};
        vm.isValid = {};
        vm.user = {};
        vm.isFormError = false;

        vm.changepassContainer = angular.element('.update-profile-card');

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
        // function to update Profile
        vm.updateProfile = function(resetconfirmFormValid) {
          if(resetconfirmFormValid){

            vm.startLoader("Updating Your Profile");
            var parameters = {};
            parameters.url = 'auth/user/';
            parameters.method = 'PUT';
            parameters.data = {
                "username": vm.user.username,
                "first_name": vm.user.first_name,
                "last_name": vm.user.last_name,
                "uid": $state.params.user_id,
            };
            parameters.token = userKey;
                parameters.callback = {
                    onSuccess: function(response) {
                        if (response.status == 200) {
                            $rootScope.notify("success", "Profile Updated Successfully!");
                            // navigate to profile page
                            $state.go('web.profile');
                            vm.stopLoader();
                        }
                    },
                    onError: function(response) {
                        if (response.status == 400) {
                            vm.stopLoader();
                            vm.isFormError = true;
                            var isUsername_valid, isFirstname_valid, isLastname_valid;
                       try {
                                isUsername_valid = typeof(response.data.username) !== 'undefined' ? true : false;
                                isFirstname_valid = typeof(response.data.email) !== 'undefined' ? true : false;
                                isLastname_valid = typeof(response.data.password1) !== 'undefined' ? true : false;
                                if (isUsername_valid) {
                                    vm.FormError = response.data.username[0];
                                } else if (isFirstname_valid) {
                                    vm.FormError = response.data.first_name[0];
                                } else if (isLastname_valid) {
                                    vm.FormError = response.data.last_name[0];

                                } else {
                                    console.log("Unhandled Error");
                                }

                            } catch (error) { // jshint ignore:line
                                console.log(error);
                            }
                        }
                        
                        vm.stopLoader();
                    }
                };

                utilities.sendRequest(parameters);

            }else {
              console.log("Form fields are not valid !");
              vm.stopLoader();
            }
        };
    }

})();
