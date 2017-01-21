// Invoking IIFE for auth
(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('AuthCtrl', AuthCtrl);

    AuthCtrl.$inject = ['utilities', 'validationSvc', '$state', '$rootScope', '$timeout'];

    function AuthCtrl(utilities, validationSvc, $state, $rootScope, $timeout) {
        var vm = this;

        vm.isRem = false;
        vm.isMail = true;
        vm.userMail = '';
        // getUser for signup
        vm.regUser = {};
        // useDetails for login
        vm.getUser = {};
        vm.isResetPassword = false;
        // form error
        vm.isFormError = false;
        vm.FormError = {};


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
                if (parameters.data.username == undefined || parameters.data.email == undefined || parameters.data.password1 == undefined || parameters.data.password2 == undefined) {
                    vm.confirmMsg = "All the fields are required !";
                    vm.stopLoader();
                } else {
                    var passwordCheck = validationSvc.password_check(parameters.data.password1, parameters.data.password2);
                    if (passwordCheck.status) {
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
                    } else {
                        vm.confirmMsg = passwordCheck.confirmMsg;
                        vm.stopLoader();
                    }
                }
            }
            // login user
        vm.userLogin = function(loginFormValid) {
            if (loginFormValid) {
                vm.isValid = {};
                var token = null;
                vm.startLoader("Taking you to EvalAI!");

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
                        console.log(response);
                        if (response.status == 200) {
                            utilities.storeData('userKey', response.data.token);
                            $state.go('web.dashboard');
                            vm.stopLoader();
                        } else {
                            alert("Something went wrong");
                            vm.stopLoader();
                        }
                    },
                    onError: function(response) {
                        if (response.status == 400) {
                            vm.isFormError = true;
                            var non_field_errors;
                            try {
                                non_field_errors = typeof(response.data.non_field_errors) !== 'undefined' ? true : false;
                                if (non_field_errors) {
                                    vm.FormError = response.data.non_field_errors[0];
                                } else {
                                    console.log("Unhandled error");
                                }
                            } catch (error) {
                                console.log(error);
                            }
                        }
                        vm.stopLoader();
                    }
                };
                utilities.sendRequest(parameters, "no-header");
            } else {
                console.log("Form fields are not valid !");
                vm.stopLoader();
            }
        }

        // function to Verify Email
        vm.verifyEmail = function() {
            vm.startLoader("Verifying Your Email");
            var parameters = {};
            parameters.url = 'auth/registration/account-confirm-email/' + $state.params.email_conf_key + '/';
            parameters.method = 'GET';
            parameters.callback = {
                onSuccess: function(response) {
                    vm.email_verify_msg = "Your email has been verified successfully";
                    vm.stopLoader();
                },
                onError: function(response) {
                    vm.email_verify_msg = "Something went wrong!! Please try again.";
                    vm.stopLoader();
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

            var passwordCheck = validationSvc.password_check(parameters.data.new_password1, parameters.data.new_password2);
            if (passwordCheck.status) {
                parameters.callback = {
                    onSuccess: function(response) {
                        var status = response.status;
                        var response = response.data;
                        vm.isResetPassword = true;
                        vm.deliveredMsg = response.detail;
                        vm.stopLoader();
                    },
                    onError: function(response) {
                        var status = response.status;
                        var error = response.data;
                        var token_valid, password1_valid, password2_valid;
                        try {
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
            } else {
                vm.deliveredMsg = passwordCheck.confirmMsg;
                vm.stopLoader();
            }
        }
    }

})();
