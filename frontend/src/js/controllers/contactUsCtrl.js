// Invoking IIFE for contact us

(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('contactUsCtrl', contactUsCtrl);

    contactUsCtrl.$inject = ['utilities', '$state', '$http', '$rootScope'];

    function contactUsCtrl(utilities, $state, $http, $rootScope) {
        var vm = this;
        var userKey = utilities.getData('userKey');
        vm.wrnMsg = {};
        vm.isValid = {};
        vm.user = {};
        vm.isFormError = false;

        vm.startLoader = function(msg) {
            $rootScope.isLoader = true;
            $rootScope.loaderTitle = msg;
        };

        // stop loader
        vm.stopLoader = function() {
            $rootScope.isLoader = false;
            $rootScope.loaderTitle = '';
        };

        // To get the previous profile data
        var parameters = {};
        parameters.url = 'web/contact/';
        parameters.method = 'GET';
        parameters.token = userKey;
        parameters.callback = {
            onSuccess: function(response) {
                var status = response.status;
                var result = response.data;
                if (status == 200) {
                    vm.user = result;
                    vm.isDisabled = true;
                }
            },
            onError: function() {
            }
        };

        utilities.sendRequest(parameters);

        // function to post data in contact us form
        vm.contactUs = function(resetconfirmFormValid) {
            if (resetconfirmFormValid) {

                var parameters = {};
                vm.isDisabled = false;
                parameters.url = 'web/contact/';
                parameters.method = 'POST';
                parameters.data = {
                    "name": vm.user.name,
                    "email": vm.user.email,
                    "message": vm.user.message,
                };
                parameters.callback = {
                    onSuccess: function(response) {
                        if (response.status == 201) {
                            var message = response.data.message;
                            $rootScope.notify("success", message);
                            // navigate to home page
                            $state.go('home');
                            vm.stopLoader();
                        }
                    },
                    onError: function(response) {
                        if (response.status == 400) {
                            vm.stopLoader();
                            vm.isFormError = true;
                            var isUsernameValid, isEmailValid, isMessageValid;
                            try {
                                isUsernameValid = typeof(response.data.name) !== 'undefined' ? true : false;
                                isEmailValid = typeof(response.data.email) !== 'undefined' ? true : false;
                                isMessageValid = typeof(response.data.message) !== 'undefined' ? true : false;
                                if (isUsernameValid) {
                                    vm.FormError = response.data.name[0];
                                } else if (isEmailValid) {
                                    vm.FormError = response.data.email[0];
                                } else if (isMessageValid) {
                                    vm.FormError = response.data.message[0];

                                } else {
                                    $rootScope.notify("error", "Some error have occured . Please try again !");
                                }

                            } catch (error) {
                                $rootScope.notify("error", "Some error have occured . Please try again !");
                            }
                        }

                        vm.stopLoader();
                    }
            };

                    utilities.sendRequest(parameters);
            }
        };
    }

})();
