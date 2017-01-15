// Invoking IIFE for auth
(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('AuthCtrl', AuthCtrl);

    AuthCtrl.$inject = ['utilities', '$state', '$rootScope', '$timeout'];

    function AuthCtrl(utilities, $state, $rootScope, $timeout) {
        var vm = this;

        vm.isRem = false;
        vm.isMail = true;
        vm.userMail = '';
        // getUser for signup
        vm.regUser = {};
        // useDetails for login
        vm.getUser = {};
        vm.isResetPassword = true;


        // default parameters
        vm.isLoader = false;
        vm.isPassConf = true;
        vm.wrnMsg = {};
        vm.isValid = {};
        vm.confirmMsg = '';
        $rootScope.loaderTitle = '';
        vm.loginContainer = angular.element('.auth-container');

        // show loader
        vm.startLoader = function(msg) {
            $rootScope.isLoader = true;
            $rootScope.loaderTitle = msg;
            vm.loginContainer.addClass('low-screen');
        }

        // stop loader
        vm.stopLoader = function() {
            $rootScope.isLoader = false;
            $rootScope.loaderTitle = '';
            vm.loginContainer.removeClass('low-screen');
        }

        vm.resetForm = function() {
            // getUser for signup
            vm.regUser = {};
            // useDetails for login
            vm.getUser = {};

            //reset error msg
            vm.wrnMsg = {};
        }

        vm.passwordChecksignUp = function(password1, password2) {
            var password1_len = password1.length;
            var password2_len = password2.length;

            if (password1_len >= 8 && password2_len >= 8)
            {
                if (password1 === password2)
                {
                    vm.confirmMsg = "Passwords Match !"
                    return true;
                }
                else {
                    vm.confirmMsg = "Passwords do not Match !"
                    vm.stopLoader();
                    return false;
                }
            }
            else {
                vm.confirmMsg = "Password is less than 8 characters !"
                vm.stopLoader();
            }
        }

        // getting signup
        vm.userSignUp = function() {
            vm.isValid = {};
            var msg = "Setting up your details!"
            vm.startLoader(msg);

            // call utility service
            var parameters = {};
            parameters.url = 'auth/registration/';
            parameters.method = 'POST';
            parameters.data = {
                "username": vm.regUser.name,
                "password1": vm.regUser.password,
                "password2": vm.regUser.confirm,
                "email": vm.regUser.email
            }
            vm.passwordsignUp = vm.passwordChecksignUp(parameters.data.password1, parameters.data.password2);
            if (vm.passwordsignUp)
            {
                parameters.callback = {
                    onSuccess: function(response) {
                        var status = response.status;
                        var response = response.data;
                        if (status == 201) {
                            vm.regUser = {};
                            vm.wrnMsg = {};
                            vm.isValid = {};
                            vm.confirmMsg = ''
                            vm.regMsg = "Registered successfully, Login to continue!";
                            $state.go('auth.login');
                            vm.stopLoader();
                        } else {
                            alert("Network Problem");
                            vm.stopLoader();
                        }
                    },
                    onError: function(response) {
                        var status = response.status;
                        var error = response.data;
                        if (status == 400) {
                            vm.stopLoader();
                            vm.isConfirm = false;
                            vm.confirmMsg = "Please correct above marked fields!"
                            angular.forEach(error, function(value, key) {
                                if (key == 'email') {
                                    vm.isValid.email = true;
                                    vm.wrnMsg.email = value[0]
                                }
                                if (key == 'password1') {
                                    vm.isValid.password = true;
                                    vm.wrnMsg.password = value[0];
                                }
                                if (key == 'password2' || key == 'non_field_errors') {
                                    vm.isValid.confirm = true;
                                    vm.wrnMsg.confirm = value[0];
                                }
                                if (key == 'username') {
                                    vm.isValid.username = true;
                                    vm.wrnMsg.username = value[0];
                                }
                            })
                            vm.stopLoader();
                        }
                    }
                };

                    utilities.sendRequest(parameters, "no-header");
            }
            else {
                confirmMsg = "Please fill the details carefully."
                vm.stopLoader();
            }
        }

        // login user
        vm.userLogin = function() {
            vm.isValid = {};
            var token = null;
            var msg = "Taking you to EvalAI!"
            vm.startLoader(msg);

            // call utility service
            var parameters = {};
            parameters.url = 'auth/login/';
            parameters.method = 'POST';
            parameters.data = {
                "username": vm.getUser.name,
                "password": vm.getUser.password,
            }
            parameters.callback = {
                onSuccess: function(response) {
                    var status = response.status;
                    var response = response.data;
                    if (status == 200) {
                        vm.getUser = {};
                        vm.wrnMsg = {};
                        vm.isValid = {};
                        vm.confirmMsg = ''
                        vm.regMsg = "";
                        utilities.storeData('userKey', response.token);
                        utilities.storeData('isRem', vm.isRem);
                        token = response.key;

                        // setting timout for token (7days)
                        // var timeNow = (new Date()).getTime();
                        // utilities.storeData('tokenTime', timeNow);
                        utilities.isAuthenticated();

                        $state.go('web.dashboard');

                        vm.stopLoader();
                    } else {
                        alert("Something went wrong");
                        vm.stopLoader();
                    }
                },
                onError: function(response) {

                    var status = response.status;
                    var error = response.data;
                    if (status == 400) {
                        vm.stopLoader();
                        vm.isConfirm = false;
                        vm.wrnMsg.cred = "Please correct above marked fields!"
                        angular.forEach(error, function(value, key) {
                            if (key == 'non_field_errors') {
                                vm.isValid.cred = true;
                                vm.wrnMsg.cred = value[0]
                            }
                            if (key == 'password') {
                                vm.isValid.password = true;
                                vm.wrnMsg.password = value[0];
                            }
                            if (key == 'username') {
                                vm.isValid.username = true;
                                vm.wrnMsg.username = value[0];
                            }
                        })
                        vm.stopLoader();
                    }

                }
            };

            utilities.sendRequest(parameters, "no-header");
        }

        // function to reset password
        vm.resetPassword = function() {
            vm.startLoader("Sending Mail");
            var parameters = {};
            parameters.url = 'auth/password/reset/';
            parameters.method = 'POST';
            parameters.data = {
                "email": vm.getUser.email,
            }
            parameters.callback = {
                onSuccess: function(response) {
                    var status = response.status;
                    var response = response.data;
                    vm.isMail = false;
                    vm.getUser.error = false;
                    console.log("Password reset email sent to the user");
                    console.log(response);
                    vm.deliveredMsg = response.success;
                    vm.getUser.email = '';
                    vm.wrnMsg = {};
                    vm.stopLoader();

                },
                onError: function(response) {
                    var status = response.status;
                    var error = response.data;
                    vm.getUser.error = "Failed";
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
                    vm.stopLoader();
                }
            };

            utilities.sendRequest(parameters, "no-header");
        }

        // function to reset password confirm
        vm.resetPasswordConfirm = function() {
            vm.startLoader("Resetting Your Password");
            var parameters = {};
            parameters.url = 'auth/password/reset/confirm/';
            parameters.method = 'POST';
            parameters.data = {
                "new_password1": vm.getUser.new_password1,
                "new_password2": vm.getUser.new_password2,
                "uid": $state.params.user_id,
                "token": $state.params.reset_token,
            }
            parameters.callback = {
                onSuccess: function(response) {
                    var status = response.status;
                    var response = response.data;
                    vm.isResetPassword = false;
                    vm.deliveredMsg = response.detail;
                    vm.stopLoader();
                    $timeout(function() {
                        $state.go("auth.login");
                    }, 2000);
                },
                onError: function(response) {
                    var status = response.status;
                    var error = response.data;
                    var token_valid, password1_valid, password2_valid;
                    try {
                        vm.isResetPassword = false;
                        token_valid = typeof(response.data.token) !== 'undefined' ? true : false;
                        password1_valid = typeof(response.data.new_password1) !== 'undefined' ? true : false;
                        password2_valid = typeof(response.data.new_password2) !== 'undefined' ? true : false;
                        if (token_valid) {
                            vm.deliveredMsg = "this link has been already used or expired.";
                        } else if (password1_valid) {
                            vm.deliveredMsg = response.data.new_password1[0] + " " + response.data.new_password1[1];
                        } else if (password2_valid) {
                            vm.deliveredMsg = response.data.new_password2[0] + " " + response.data.new_password2[1];
                        } else {
                            console.log("Unhandled Error");
                        }
                    } catch (error) {
                        vm.deliveredMsg = "Something went wrong! Please refresh the page and try again.";
                    }
                    vm.stopLoader();
                }
            };

            utilities.sendRequest(parameters, "no-header");
        }
    }

})();
