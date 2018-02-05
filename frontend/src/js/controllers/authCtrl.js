// Invoking IIFE for auth
(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('AuthCtrl', AuthCtrl);

    AuthCtrl.$inject = ['utilities', '$state', '$rootScope', '$timeout'];

    function AuthCtrl(utilities, $state, $rootScope) {
        var vm = this;

        vm.isRem = false;
        vm.isAuth = false;
        vm.isMail = true;
        vm.userMail = '';
        // getUser for signup
        vm.regUser = {};
        // useDetails for login
        vm.getUser = {};
        // color to show password strength
        vm.color = {};
        vm.isResetPassword = false;
        // form error
        vm.isFormError = false;
        vm.FormError = {};
        // to store the next redirect route
        vm.redirectUrl = {};

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
        };

        // stop loader
        vm.stopLoader = function() {
            $rootScope.isLoader = false;
            $rootScope.loaderTitle = '';
            vm.loginContainer.removeClass('low-screen');
        };

        vm.resetForm = function() {
            // getUser for signup
            vm.regUser = {};
            // useDetails for login
            vm.getUser = {};

            //reset error msg
            vm.wrnMsg = {};

            //switch off form errors
            vm.isFormError = false;

            //reset form when link sent for reset password
            vm.isMail = true;
        };

        // Function to signup
        vm.userSignUp = function(signupFormValid) {
            if (signupFormValid) {
                vm.startLoader("Setting up your details!");
                // call utility service
                var parameters = {};
                parameters.url = 'auth/registration/';
                parameters.method = 'POST';
                parameters.data = {
                    "username": vm.regUser.name,
                    "password1": vm.regUser.password,
                    "password2": vm.regUser.confirm_password,
                    "email": vm.regUser.email
                };
                parameters.callback = {
                    onSuccess: function(response) {
                        if (response.status == 201) {
                            vm.isFormError = false;
                            // vm.regMsg = "Registered successfully, Login to continue!";
                            $rootScope.notify("success", "Registered successfully. Please verify your email address!");
                            $state.go('auth.login');
                        }
                        vm.stopLoader();
                    },
                    onError: function(response) {
                        if (response.status == 400) {
                            vm.stopLoader();
                            vm.isFormError = true;
                            var non_field_errors, isUsername_valid, isEmail_valid, isPassword1_valid, isPassword2_valid;
                            try {
                                non_field_errors = typeof(response.data.non_field_errors) !== 'undefined' ? true : false;
                                isUsername_valid = typeof(response.data.username) !== 'undefined' ? true : false;
                                isEmail_valid = typeof(response.data.email) !== 'undefined' ? true : false;
                                isPassword1_valid = typeof(response.data.password1) !== 'undefined' ? true : false;
                                isPassword2_valid = typeof(response.data.password2) !== 'undefined' ? true : false;
                                if (non_field_errors) {
                                    vm.FormError = response.data.non_field_errors[0];
                                } else if (isUsername_valid) {
                                    vm.FormError = response.data.username[0];
                                } else if (isEmail_valid) {
                                    vm.FormError = response.data.email[0];
                                } else if (isPassword1_valid) {
                                    vm.FormError = response.data.password1[0];
                                } else if (isPassword2_valid) {
                                    vm.FormError = response.data.password2[0];

                                }

                            } catch (error) {
                                $rootScope.notify("error", error);
                            }
                        }

                        vm.stopLoader();
                    }
                };
                utilities.sendRequest(parameters, "no-header");
            } else {
                vm.stopLoader();
            }
        };

        // Function to login
        vm.userLogin = function(loginFormValid) {
            if (loginFormValid) {
                vm.startLoader("Taking you to EvalAI!");
                // call utility service
                var parameters = {};
                parameters.url = 'auth/login/';
                parameters.method = 'POST';
                parameters.data = {
                    "username": vm.getUser.name,
                    "password": vm.getUser.password,
                };
                parameters.callback = {
                    onSuccess: function(response) {
                        if (response.status == 200) {
                            utilities.storeData('userKey', response.data.token);
                            if ($rootScope.previousState) {
                                $state.go($rootScope.previousState);
                                vm.stopLoader();
                            } else {
                                $state.go('web.dashboard');
                            }
                        } else {
                            alert("Something went wrong");
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
                                }
                            } catch (error) {
                                $rootScope.notify("error", error);
                            }
                        }
                        vm.stopLoader();
                    }
                };
                utilities.sendRequest(parameters, "no-header");
            } else {
                vm.stopLoader();
            }
        };


        // function to check password strength
        vm.checkStrength = function(password) {
            var passwordStrength = utilities.passwordStrength(password);
            vm.message = passwordStrength[0];
            vm.color = passwordStrength[1];
        };

        // function to Verify Email
        vm.verifyEmail = function() {
            vm.startLoader("Verifying Your Email");
            var parameters = {};
            parameters.url = 'auth/registration/account-confirm-email/' + $state.params.email_conf_key + '/';
            parameters.method = 'GET';
            parameters.callback = {
                onSuccess: function() {
                    vm.email_verify_msg = "Your email has been verified successfully";
                    vm.stopLoader();
                },
                onError: function() {
                    vm.email_verify_msg = "Something went wrong!! Please try again.";
                    vm.stopLoader();
                }
            };

            utilities.sendRequest(parameters, "no-header");
        };

        // function to reset password
        vm.resetPassword = function(resetPassFormValid) {
            if (resetPassFormValid) {
                vm.startLoader("Sending Mail");
                var parameters = {};
                parameters.url = 'auth/password/reset/';
                parameters.method = 'POST';
                parameters.data = {
                    "email": vm.getUser.email,
                };
                parameters.callback = {
                    onSuccess: function(response) {
                        vm.isMail = false;
                        vm.getUser.error = false;
                        vm.isFormError = false;
                        vm.deliveredMsg = response.data.success;
                        vm.getUser.email = '';
                        vm.stopLoader();
                    },
                    onError: function() {
                        vm.isFormError = true;
                        vm.FormError = "Something went wrong. Please try again";
                        vm.stopLoader();
                    }
                };
                utilities.sendRequest(parameters, "no-header");
            } else {
                vm.stopLoader();
            }
        };

        // function to reset password confirm
        vm.resetPasswordConfirm = function(resetconfirmFormValid) {
            if (resetconfirmFormValid) {
                vm.startLoader("Resetting Your Password");
                var parameters = {};
                parameters.url = 'auth/password/reset/confirm/';
                parameters.method = 'POST';
                parameters.data = {
                    "new_password1": vm.getUser.new_password1,
                    "new_password2": vm.getUser.new_password2,
                    "uid": $state.params.user_id,
                    "token": $state.params.reset_token,
                };

                parameters.callback = {
                    onSuccess: function(response) {
                        var details = response.data;
                        vm.isResetPassword = true;
                        vm.deliveredMsg = details.detail;
                        vm.stopLoader();
                    },
                    onError: function(response) {
                        var token_valid, password1_valid, password2_valid;
                        vm.isFormError = true;
                        try {
                            token_valid = typeof(response.data.token) !== 'undefined' ? true : false;
                            password1_valid = typeof(response.data.new_password1) !== 'undefined' ? true : false;
                            password2_valid = typeof(response.data.new_password2) !== 'undefined' ? true : false;
                            if (token_valid) {
                                vm.FormError = "this link has been already used or expired.";
                            } else if (password1_valid) {
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

                utilities.sendRequest(parameters, "no-header");
            } else {
                vm.stopLoader();
            }
        };

        $rootScope.$on('$stateChangeStart', function() {
            vm.resetForm();
        });
    }
})();
