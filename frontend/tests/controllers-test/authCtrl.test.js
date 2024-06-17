'use strict';

describe('Unit tests for auth controller', function () {
    beforeEach(angular.mock.module('evalai'));

    var $controller, $rootScope, $state, $window, $scope, utilities, vm;

    beforeEach(inject(function (_$controller_, _$rootScope_, _$state_, _utilities_) {
        $controller = _$controller_;
        $rootScope = _$rootScope_;
        $state = _$state_;
        utilities = _utilities_;

        $scope = $rootScope.$new();
        vm = $controller('AuthCtrl', {$scope: $scope});
    }));

    describe('Global Variables', function () {
        it('has default values', function () {
            expect(vm.isRem).toEqual(false);
            expect(vm.isAuth).toEqual(false);
            expect(vm.isMail).toEqual(true);
            expect(vm.userMail).toEqual('');
            expect(vm.regUser).toEqual({});
            expect(vm.getUser).toEqual({});
            expect(vm.color).toEqual({});
            expect(vm.isResetPassword).toEqual(false);
            expect(vm.isFormError).toEqual(false);
            expect(vm.FormError).toEqual({});
            expect(vm.redirectUrl).toEqual({});
            expect(vm.isLoader).toEqual(false);
            expect(vm.isPassConf).toEqual(true);
            expect(vm.wrnMsg).toEqual({});
            expect(vm.isValid).toEqual({});
            expect(vm.confirmMsg).toEqual('');
            expect($rootScope.loaderTitle).toEqual('');
        });
    });

    describe('Validate helper functions', function () {
        it('startLoader', function () {
            var message = 'Start Loader';
            vm.startLoader(message);
            expect($rootScope.isLoader).toEqual(true);
            expect($rootScope.loaderTitle).toEqual(message);
        });

        it('stopLoader', function () {
            var message = '';
            vm.stopLoader();
            expect($rootScope.isLoader).toEqual(false);
            expect($rootScope.loaderTitle).toEqual(message);
        });

        it('resetForm', function () {
            vm.resetForm();
            expect(vm.regUser).toEqual({});
            expect(vm.getUser).toEqual({});
            expect(vm.wrnMsg).toEqual({});
            expect(vm.isFormError).toEqual(false);
            expect(vm.isMail).toEqual(true);
        });
    });

    describe('Unit tests for userSignUp function `auth/registration/`', function () {
        var errors = {
            username: 'username error',
            email: 'email error',
            password1: 'password error',
            password2: 'password confirm error'
        };

        beforeEach(function () {
            vm.regUser = {
                username: 'ford',
                email: 'fordprefect@hitchhikers.guide',
                password1: 'dontpanic',
                password2: 'dontpanic'
            };

            utilities.sendRequest = function (parameters) {
                var data, status;
                var emailRegex = /\S+@\S+\.\S+/;
                var usernameRegex = /^[a-zA-Z0-9]{3,30}$/;
                var passwordRegex = /^[a-zA-Z0-9!@#$%^&*_]{8,30}$/;
                var isUsernameValid = usernameRegex.test(parameters.username);
                var isEmailValid = emailRegex.test(parameters.email);
                var isPassword1Valid = passwordRegex.test(parameters.password1);
                var isPassword2Valid = passwordRegex.test(parameters.password2);
                if (!isUsernameValid || !isEmailValid || !isPassword1Valid || !isPassword2Valid) {
                    if (!isUsernameValid) {
                        data = errors.username;
                    } else if (!isEmailValid) {
                        data = errors.email;
                    } else if (!isPassword1Valid || !isPassword2Valid) {
                        data = errors.password1;
                    }
                    status = 400;
                } else if (parameters.password1 != parameters.password2) {
                    data = errors.password2;
                    status = 400;
                } else {
                    data = "success";
                    status = 201;
                }
                return {
                    "data": data,
                    "status": parseInt(status)
                };
            };
        });

        it('correct sign up details', function () {
            vm.userSignUp(true);
            var response = utilities.sendRequest(vm.regUser);
            expect(response.status).toEqual(201);
            expect(response.data).toEqual("success");
        });

        it('missing username', function () {
            vm.regUser.username = '';
            var response = utilities.sendRequest(vm.regUser);
            expect(response.status).toEqual(400);
            expect(response.data).toEqual(errors.username);
        });

        it('missing email', function () {
            vm.regUser.email = '';
            var response = utilities.sendRequest(vm.regUser);
            expect(response.status).toEqual(400);
            expect(response.data).toEqual(errors.email);
        });

        it('missing password', function () {
            vm.regUser.password1 = '';
            var response = utilities.sendRequest(vm.regUser);
            expect(response.status).toEqual(400);
            expect(response.data).toEqual(errors.password1);
        });

        it('mismatch password', function () {
            vm.regUser.password2 = 'failword';
            var response = utilities.sendRequest(vm.regUser);
            expect(response.status).toEqual(400);
            expect(response.data).toEqual(errors.password2);
        });

        it('invalid details', function () {
            vm.userSignUp(false);
            expect($rootScope.isLoader).toEqual(false);
        });
    });
    describe('Unit tests for userLogin function `auth/login/`', function () {
        var errors = {
            non_field_errors: 'Unable to log in with provided credentials.'
        };
    
        beforeEach(function () {
            vm.getUser = {
                username: 'ford',
                password: 'dontpanic',
            };
    
            utilities.sendRequest = function (parameters) {
                if (parameters.callback) {
                    if (parameters.url === 'auth/login/' && parameters.method === 'POST') {
                        var usernameRegex = /^[a-zA-Z0-9]+$/;
                        var passwordRegex = /^[a-zA-Z0-9!@#$%^&*_]{8,30}$/;
                        var isUsernameValid = usernameRegex.test(vm.getUser.username);
                        var isPasswordValid = passwordRegex.test(vm.getUser.password);
                        if (!isUsernameValid || !isPasswordValid) {
                            parameters.callback.onError({data: {non_field_errors: errors.non_field_errors}});
                        } else {
                            parameters.callback.onSuccess({data: "success"});
                        }
                    }
                }
            };
        });
    
        it('handles successful login', function () {
            vm.userLogin(true);
            expect($rootScope.isLoader).toBe(true);
            expect(vm.isAuth).toBe(false);
        });
    
        it('handles error on login', function () {
            errors.non_field_errors = 'Unable to log in with provided credentials.';
    
            spyOn(vm, 'userLogin').and.callFake(function() {
                vm.FormError = { non_field_errors: errors.non_field_errors };
                vm.isFormError = true; 
            });
            vm.getUser.username = '';
            vm.userLogin(true);
    
            expect($rootScope.isLoader).toBe(undefined);
            expect(vm.isFormError).toBe(true);
            expect(vm.FormError.non_field_errors).toBe(errors.non_field_errors);
        });
    });


    describe('Unit tests for userSignUp function `auth/registration/`', function () {
        var errors = {
            username: 'username error',
            email: 'email error',
            password1: 'password error',
            password2: 'password confirm error'
        };
    
        beforeEach(function () {
            vm.regUser = {
                username: 'ford',
                email: 'fordprefect@hitchhikers.guide',
                password1: 'dontpanic',
                password2: 'dontpanic'
            };
    
            utilities.sendRequest = function (parameters) {
                if (parameters.callback) {
                    if (parameters.url === 'auth/registration/' && parameters.method === 'POST') {
                        var emailRegex = /\S+@\S+\.\S+/;
                        var usernameRegex = /^[a-zA-Z0-9]{3,30}$/;
                        var passwordRegex = /^[a-zA-Z0-9!@#$%^&*_]{8,30}$/;
                        var isUsernameValid = usernameRegex.test(vm.regUser.username);
                        var isEmailValid = emailRegex.test(vm.regUser.email);
                        var isPassword1Valid = passwordRegex.test(vm.regUser.password1);
                        var isPassword2Valid = passwordRegex.test(vm.regUser.password2);
                        if (!isUsernameValid) {
                            parameters.callback.onError({data: {username: errors.username}});
                        } else if (!isEmailValid) {
                            parameters.callback.onError({data: {email: errors.email}});
                        } else if (!isPassword1Valid) {
                            parameters.callback.onError({data: {password1: errors.password1}});
                        } else if (vm.regUser.password1 !== vm.regUser.password2) {
                            parameters.callback.onError({data: {password2: errors.password2}});
                        } else {
                            parameters.callback.onSuccess({data: "success"});
                        }
                    }
                }
            };
        });
    
        it('handles successful signup', function () {
            vm.userSignUp(true);
            expect($rootScope.isLoader).toBe(false);
            expect(vm.isAuth).toBe(false);
        });
        it('handles error on username', function () {
            errors.username = 'username error';
            spyOn(vm, 'userSignUp').and.callFake(function() {
                vm.FormError = { username: errors.username };
            });
            vm.regUser.username = '';
            vm.userSignUp(true);
            expect($rootScope.isLoader).toBe(undefined);    
            expect(vm.isFormError).toBe(false);
            expect(vm.FormError.username).toBe(errors.username);
        });
        it('handles error on email', function () {
            errors.email = 'email error';
            spyOn(vm, 'userSignUp').and.callFake(function() {
                vm.FormError = { email: errors.email };
            });
            vm.regUser.email = '';
            vm.userSignUp(true);
            expect($rootScope.isLoader).toBe(undefined);
            expect(vm.isFormError).toBe(false);
            expect(vm.FormError.email).toBe(errors.email);
        });
    });

    describe('Unit tests for checkPasswordStrength', function () {

        var passWordsTestsList = [
            {
                password: 'password',
                passwordValidator: 1,
                expectedStrength: "Weak",
                expectedColor: "red"
            },
            {
                password: 'password123',
                passwordValidator: 2,
                expectedStrength: "Average",
                expectedColor: "darkorange"
            },
            {
                password: 'pWord1',
                passwordValidator: 3,
                expectedStrength: "Good",
                expectedColor: "green"
            },
            {
                password: 'passwordLength123',
                passwordValidator: 4,
                expectedStrength: "Strong",
                expectedColor: "darkgreen"
            },
            {
                password: '#passwordLength123',
                passwordValidator: 5,
                expectedStrength: "Very Strong",
                expectedColor: "darkgreen"
            },
        ];


        beforeEach(function () {
            utilities.passwordStrength = function (password) {
                //Regular Expressions.  
                var regex = new Array();
                regex.push("[A-Z]", "[a-z]", "[0-9]", "[$$!%*#?&]");

                var passed = 0;
                //Validate for each Regular Expression.  
                for (var i = 0; i < regex.length; i++) {
                    if (new RegExp(regex[i]).test(password)) {
                        passed++;
                    }
                }
                //Validate for length of Password.  
                if (passed > 2 && password.length > 8) {
                    passed++;
                }

                for (var i = 0; i < passWordsTestsList.length; i++) {
                    if (passWordsTestsList[i].passwordValidator == passed) {
                        return [passWordsTestsList[i].expectedStrength, passWordsTestsList[i].expectedColor];
                    }
                }
            };
        });

        passWordsTestsList.forEach(passWord => {
            it(passWord.password + ' should have a strength & color of : ' + passWord.expectedStrength + ':' + passWord.expectedColor, () => {
                var passwordStrength = utilities.passwordStrength(passWord.password);
                expect(passwordStrength[0]).toEqual(passWord.expectedStrength);
                expect(passwordStrength[1]).toEqual(passWord.expectedColor);
            });
        });
    });

    describe('Unit tests for verifyEmail function `auth/registration/account-confirm-email/<email_conf_key>/`', function () {
        var verified;

        beforeEach(function () {
            utilities.sendRequest = function (parameters) {
                if (verified) {
                    parameters.callback.onSuccess();
                } else {
                    parameters.callback.onError();
                }
            };
        });

        it('correct email', function () {
            verified = true;
            vm.verifyEmail();
            expect(vm.email_verify_msg).toEqual('Your email has been verified successfully');
        });

        it('incorrect email', function () {
            verified = false;
            vm.verifyEmail();
            expect(vm.email_verify_msg).toEqual('Something went wrong!! Please try again.');
        });
    });

    describe('Unit tests for resetPassword function `auth/password/reset/`', function () {
        var success;
        var inactiveResponse = 'Account is not active. Please contact the administrator.';
        var mailSent = 'mail sent';

        beforeEach(function () {
            utilities.sendRequest = function (parameters) {
                if (success) {
                    parameters.callback.onSuccess({
                        data: {
                            success: mailSent
                        }
                    });
                } else {
                    parameters.callback.onError({status: 400, data: {details: inactiveResponse}});
                }
            };
        });

        it('sent successfully', function () {
            success = true;
            vm.resetPassword(true);
            expect(vm.isFormError).toEqual(false);
            expect(vm.deliveredMsg).toEqual(mailSent);
        });

        it('backend error', function () {
            success = false;
            vm.resetPassword(true);
            expect(vm.isFormError).toEqual(true);
            expect(vm.FormError).toEqual(inactiveResponse);
        });

        it('invalid details', function () {
            vm.resetPassword(false);
            expect($rootScope.isLoader).toEqual(false);
        });
    });

    describe('Unit tests for resetPasswordConfirm function `auth/password/reset/confirm/`', function () {
        var success;

        var resetConfirm = 'password reset confirmed';

        beforeEach(function () {
            utilities.sendRequest = function (parameters) {
                if (success) {
                    parameters.callback.onSuccess({
                        data: {
                            detail: resetConfirm
                        }
                    });
                } else {
                    parameters.callback.onError();
                }
            };
        });

        it('successful reset', function () {
            $state.params.user_id = 42;
            $state.params.reset_token = 'secure';
            success = true;
            vm.resetPasswordConfirm(true);
            expect(vm.isResetPassword).toEqual(true);
            expect(vm.deliveredMsg).toEqual(resetConfirm);
        });

        it('backend error', function () {
            $state.params.user_id = 42;
            success = false;
            vm.resetPasswordConfirm(true);
            expect(vm.isFormError).toEqual(true);
        });

        it('invalid details', function () {
            vm.resetPasswordConfirm(false);
            expect($rootScope.isLoader).toEqual(false);
        });
        it('should toggle canShowPassword', function() {
            $rootScope.canShowPassword = false;
            vm.togglePasswordVisibility();
            expect($rootScope.canShowPassword).toEqual(true);
            vm.togglePasswordVisibility();
            expect($rootScope.canShowPassword).toEqual(false);
        });
        
        it('should toggle canShowConfirmPassword', function() {
            $rootScope.canShowConfirmPassword = false;
            vm.toggleConfirmPasswordVisibility();
            expect($rootScope.canShowConfirmPassword).toEqual(true);
            vm.toggleConfirmPasswordVisibility();
            expect($rootScope.canShowConfirmPassword).toEqual(false);
        });
    });

    describe('Unit tests for userSignUp function `auth/registration/`', function () {
        var errors = {
            username: 'username error',
            email: 'email error',
            password1: 'password error',
            password2: 'password confirm error'
        };

        beforeEach(function () {
            vm.regUser = {
                name: 'ford',
                email: 'fordprefect@hitchhikers.guide',
                password: 'dontpanic',
                confirm_password: 'dontpanic'
            };

            utilities.sendRequest = function (parameters) {
                if (parameters.url === 'auth/registration/') {
                    var emailRegex = /\S+@\S+\.\S+/;
                    var usernameRegex = /^[a-zA-Z0-9]{3,30}$/;
                    var passwordRegex = /^[a-zA-Z0-9!@#$%^&*_]{8,30}$/;
                    var isUsernameValid = usernameRegex.test(parameters.data.username);
                    var isEmailValid = emailRegex.test(parameters.data.email);
                    var isPassword1Valid = passwordRegex.test(parameters.data.password1);
                    var isPassword2Valid = passwordRegex.test(parameters.data.password2);
                    if (!isUsernameValid || !isEmailValid || !isPassword1Valid || !isPassword2Valid) {
                        var data;
                        if (!isUsernameValid) {
                            data = {username: [errors.username]};
                        } else if (!isEmailValid) {
                            data = {email: [errors.email]};
                        } else if (!isPassword1Valid || !isPassword2Valid) {
                            data = {password1: [errors.password1]};
                        }
                        parameters.callback.onError({status: 400, data: data});
                    } else if (parameters.data.password1 !== parameters.data.password2) {
                        parameters.callback.onError({status: 400, data: {password2: [errors.password2]}});
                    } else {
                        parameters.callback.onSuccess({status: 201});
                    }
                } else if (parameters.url === 'auth/login/') {
                    parameters.callback.onSuccess({status: 200, data: {token: 'fake-token'}});
                }
            };
        });

        it('should handle successful signup', function () {
            spyOn($rootScope, 'notify');
            spyOn($state, 'go');

            vm.userSignUp(true);
            expect($rootScope.notify).toHaveBeenCalledWith("success", "Registered successfully. Please verify your email address!");
            expect($state.go).toHaveBeenCalledWith('web.dashboard');
        });

        it('should handle signup failure with username error', function () {
            spyOn($rootScope, 'notify');

            vm.regUser.name = '';
            vm.userSignUp(true);
            expect(vm.isFormError).toEqual(true);
            expect(vm.FormError).toEqual(errors.username);
        });

        it('should handle signup failure with email error', function () {
            spyOn($rootScope, 'notify');

            vm.regUser.email = '';
            vm.userSignUp(true);
            expect(vm.isFormError).toEqual(true);
            expect(vm.FormError).toEqual(errors.email);
        });

        it('should handle signup failure with password error', function () {
            spyOn($rootScope, 'notify');

            vm.regUser.password = '';
            vm.userSignUp(true);
            expect(vm.isFormError).toEqual(true);
            expect(vm.FormError).toEqual(errors.password1);
        });

        it('should handle signup failure with password mismatch error', function () {
            spyOn($rootScope, 'notify');

            vm.regUser.confirm_password = 'mismatch';
            vm.userSignUp(true);
            expect(vm.isFormError).toEqual(true);
            expect(vm.FormError).toEqual(errors.password2);
        });

        it('should handle invalid form submission', function () {
            vm.userSignUp(false);
            expect($rootScope.isLoader).toEqual(false);
        });
    });

    describe('Unit tests for setRefreshJWT function', function () {
        beforeEach(function () {
            utilities.sendRequest = function (parameters) {
                var response;
                if (parameters.url === 'accounts/user/get_auth_token' && parameters.method === 'GET') {
                    response = {
                        status: 200,
                        data: {
                            token: 'dummyToken'
                        }
                    };
                } else {
                    response = {
                        status: 400,
                        data: {
                            non_field_errors: ['Invalid request']
                        }
                    };
                }
                if (response.status === 200) {
                    parameters.callback.onSuccess(response);
                } else {
                    parameters.callback.onError(response);
                }
            };

            spyOn(utilities, 'sendRequest').and.callThrough();
            spyOn(utilities, 'storeData').and.callThrough();
            spyOn(window, 'alert').and.callThrough();
        });

        it('should store JWT token on successful fetch', function () {
            vm.setRefreshJWT();
            expect(utilities.sendRequest).toHaveBeenCalled();
            expect(utilities.storeData).toHaveBeenCalledWith('refreshJWT', 'dummyToken');
        });

        it('should handle form errors on failed fetch with status 400', function () {
            utilities.sendRequest = function (parameters) {
                var response = {
                    status: 400,
                    data: {
                        non_field_errors: ['Invalid request']
                    }
                };
                parameters.callback.onError(response);
            };
            vm.setRefreshJWT();
            expect(vm.isFormError).toBe(true);
            expect(vm.FormError).toEqual('Invalid request');
        });
    });

    describe('Unit tests for userLogin function `auth/login/`', function () {
        var errors = {
            non_field_errors: 'Invalid credentials'
        };

        beforeEach(function () {
            vm.getUser = {
                name: 'ford',
                password: 'dontpanic'
            };

            utilities.sendRequest = function (parameters) {
                if (parameters.url === 'auth/login/') {
                    var usernameRegex = /^[a-zA-Z0-9]+$/;
                    var passwordRegex = /^[a-zA-Z0-9!@#$%^&*_]{8,30}$/;
                    var isUsernameValid = usernameRegex.test(parameters.data.username);
                    var isPasswordValid = passwordRegex.test(parameters.data.password);
                    if (!isUsernameValid || !isPasswordValid) {
                        parameters.callback.onError({status: 400, data: {non_field_errors: [errors.non_field_errors]}});
                    } else {
                        parameters.callback.onSuccess({status: 200, data: {token: 'fake-token'}});
                    }
                }
            };
        });

        it('should handle successful login', function () {
            spyOn($state, 'go');
            spyOn(utilities, 'storeData');

            vm.userLogin(true);
            expect(utilities.storeData).toHaveBeenCalledWith('userKey', 'fake-token');
            expect($state.go).toHaveBeenCalledWith('web.dashboard');
        });

        it('should handle login failure with invalid credentials', function () {
            spyOn($rootScope, 'notify');

            vm.getUser.name = '';
            vm.userLogin(true);
            expect(vm.isFormError).toEqual(true);
            expect(vm.FormError).toEqual(errors.non_field_errors);
        });

        it('should handle invalid form submission', function () {
            vm.userLogin(false);
            expect($rootScope.isLoader).toEqual(false);
        });
    });
    describe('Unit tests for checkStrength function', function () {
        var passwordStrengthCases = [
            { password: 'password', expectedMessage: 'Weak', expectedColor: 'red' },
            { password: 'password123', expectedMessage: 'Average', expectedColor: 'orange' },
            { password: 'P@ssword1', expectedMessage: 'Strong', expectedColor: 'green' }
        ];

        beforeEach(function () {
            utilities.passwordStrength = function (password) {
                if (password === '') {
                    return [null, null];
                } else if (password === 'password') {
                    return ['Weak', 'red'];
                } else if (password === 'password123') {
                    return ['Average', 'orange'];
                } else if (password === 'P@ssword1') {
                    return ['Strong', 'green'];
                }
            };
        });

        passwordStrengthCases.forEach(function (testCase) {
            it('should correctly evaluate the strength of the password: ' + testCase.password, function () {
                vm.checkStrength(testCase.password);
                expect(vm.showPasswordStrength).toEqual(true);
                expect(vm.message).toEqual(testCase.expectedMessage);
                expect(vm.color).toEqual(testCase.expectedColor);
            });
        });

        it('should hide password strength indicator for empty password', function () {
            vm.checkStrength('');
            expect(vm.showPasswordStrength).toEqual(false);
        });
    });

    describe('Unit tests for resetForm function', function () {
        it('should reset form variables correctly', function () {
            vm.resetForm();
            expect(vm.regUser).toEqual({});
            expect(vm.getUser).toEqual({});
            expect(vm.wrnMsg).toEqual({});
            expect(vm.isFormError).toEqual(false);
            expect(vm.isMail).toEqual(true);
        });
    });

    describe('Unit tests for $stateChangeStart event', function () {
        it('should call resetForm on state change', function () {
            spyOn(vm, 'resetForm');

            $rootScope.$broadcast('$stateChangeStart', { name: 'authpage' });
            expect(vm.resetForm).toHaveBeenCalled();
        });
    });
});
