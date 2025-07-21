'use strict';

describe('Unit tests for auth controller', function () {
    beforeEach(angular.mock.module('evalai'));

    var $controller, $rootScope, $state, $window, $scope, utilities, vm;

    beforeEach(inject(function (_$controller_, _$rootScope_, _$state_, _$window_, _utilities_) {
        $controller = _$controller_;
        $rootScope = _$rootScope_;
        $state = _$state_;
        $window = _$window_;
        utilities = _utilities_;

        $scope = $rootScope.$new();
        vm = $controller('AuthCtrl', { $scope: $scope });
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

        it('should handle successful signup and auto-login', function () {
            // Mock utilities.sendRequest for signup and login
            var signupCalled = false, loginCalled = false;
            utilities.sendRequest = function (parameters, header) {
                if (parameters.url === 'auth/registration/') {
                    signupCalled = true;
                    parameters.callback.onSuccess({ status: 201 });
                } else if (parameters.url === 'auth/login/') {
                    loginCalled = true;
                    parameters.callback.onSuccess({ status: 200, data: { token: 'testtoken' } });
                }
            };
            spyOn($state, 'go');
            spyOn(utilities, 'storeData');
            vm.regUser = { name: 'ford', password: 'dontpanic', confirm_password: 'dontpanic', email: 'ford@galaxy.com' };
            vm.userSignUp(true);
            expect(signupCalled).toBe(true);
            expect(loginCalled).toBe(true);
            expect(utilities.storeData).toHaveBeenCalledWith('userKey', 'testtoken');
            expect($state.go).toHaveBeenCalledWith('web.dashboard');
        });

        it('should handle login error after signup', function () {
            utilities.sendRequest = function (parameters, header) {
                if (parameters.url === 'auth/registration/') {
                    parameters.callback.onSuccess({ status: 201 });
                } else if (parameters.url === 'auth/login/') {
                    parameters.callback.onError({ status: 400, data: { non_field_errors: ['Invalid credentials'] } });
                }
            };
            vm.regUser = { name: 'ford', password: 'dontpanic', confirm_password: 'dontpanic', email: 'ford@galaxy.com' };
            vm.userSignUp(true);
            expect(vm.isFormError).toBe(true);
            expect(vm.FormError).toBe('Invalid credentials');
        });

        it('should handle signup error with non_field_errors', function () {
            utilities.sendRequest = function (parameters, header) {
                parameters.callback.onError({ status: 400, data: { non_field_errors: ['Signup error'] } });
            };
            vm.userSignUp(true);
            expect(vm.isFormError).toBe(true);
            expect(vm.FormError).toBe('Signup error');
        });

        it('should handle signup error with username error', function () {
            utilities.sendRequest = function (parameters, header) {
                parameters.callback.onError({ status: 400, data: { username: ['Username error'] } });
            };
            vm.userSignUp(true);
            expect(vm.isFormError).toBe(true);
            expect(vm.FormError).toBe('Username error');
        });

        it('should handle signup error with email error', function () {
            utilities.sendRequest = function (parameters, header) {
                parameters.callback.onError({ status: 400, data: { email: ['Email error'] } });
            };
            vm.userSignUp(true);
            expect(vm.isFormError).toBe(true);
            expect(vm.FormError).toBe('Email error');
        });

        it('should handle signup error with password1 error', function () {
            utilities.sendRequest = function (parameters, header) {
                parameters.callback.onError({ status: 400, data: { password1: ['Password1 error'] } });
            };
            vm.userSignUp(true);
            expect(vm.isFormError).toBe(true);
            expect(vm.FormError).toBe('Password1 error');
        });

        it('should handle signup error with password2 error', function () {
            utilities.sendRequest = function (parameters, header) {
                parameters.callback.onError({ status: 400, data: { password2: ['Password2 error'] } });
            };
            vm.userSignUp(true);
            expect(vm.isFormError).toBe(true);
            expect(vm.FormError).toBe('Password2 error');
        });

        it('should redirect to previousState after successful signup and login', function () {
            var signupCalled = false, loginCalled = false;
            $rootScope.previousState = 'web.profile';
            spyOn($state, 'go');
            spyOn(utilities, 'storeData');
            utilities.sendRequest = function (parameters, header) {
                if (parameters.url === 'auth/registration/') {
                    signupCalled = true;
                    parameters.callback.onSuccess({ status: 201 });
                } else if (parameters.url === 'auth/login/') {
                    loginCalled = true;
                    parameters.callback.onSuccess({ status: 200, data: { token: 'testtoken' } });
                }
            };
            vm.regUser = { name: 'ford', password: 'dontpanic', confirm_password: 'dontpanic', email: 'ford@galaxy.com' };
            vm.userSignUp(true);
            expect(signupCalled).toBe(true);
            expect(loginCalled).toBe(true);
            expect(utilities.storeData).toHaveBeenCalledWith('userKey', 'testtoken');
            expect($state.go).toHaveBeenCalledWith('web.profile');
        });

        it('should alert if login after signup returns non-200', function () {
            utilities.sendRequest = function (parameters, header) {
                if (parameters.url === 'auth/registration/') {
                    parameters.callback.onSuccess({ status: 201 });
                } else if (parameters.url === 'auth/login/') {
                    parameters.callback.onSuccess({ status: 500 });
                }
            };
            spyOn(window, 'alert');
            vm.regUser = { name: 'ford', password: 'dontpanic', confirm_password: 'dontpanic', email: 'ford@galaxy.com' };
            vm.userSignUp(true);
            expect(window.alert).toHaveBeenCalledWith('Something went wrong');
        });

        it('should handle login error after signup with exception', function () {
            utilities.sendRequest = function (parameters, header) {
                if (parameters.url === 'auth/registration/') {
                    parameters.callback.onSuccess({ status: 201 });
                } else if (parameters.url === 'auth/login/') {
                    parameters.callback.onError({ status: 400, data: null });
                }
            };
            spyOn($rootScope, 'notify');
            vm.regUser = { name: 'ford', password: 'dontpanic', confirm_password: 'dontpanic', email: 'ford@galaxy.com' };
            vm.userSignUp(true);
            expect(vm.isFormError).toBe(true);
            expect($rootScope.notify).toHaveBeenCalled();
        });


        it('should set FormError for non_field_errors on signup error', function () {
            utilities.sendRequest = function (parameters, header) {
                parameters.callback.onError({
                    status: 400,
                    data: { non_field_errors: ['A non-field error occurred'] }
                });
            };
            vm.userSignUp(true);
            expect(vm.isFormError).toBe(true);
            expect(vm.FormError).toBe('A non-field error occurred');
        });

        it('should set FormError for username error on signup error', function () {
            utilities.sendRequest = function (parameters, header) {
                parameters.callback.onError({
                    status: 400,
                    data: { username: ['Username already exists'] }
                });
            };
            vm.userSignUp(true);
            expect(vm.isFormError).toBe(true);
            expect(vm.FormError).toBe('Username already exists');
        });

        it('should set FormError for email error on signup error', function () {
            utilities.sendRequest = function (parameters, header) {
                parameters.callback.onError({
                    status: 400,
                    data: { email: ['Email already exists'] }
                });
            };
            vm.userSignUp(true);
            expect(vm.isFormError).toBe(true);
            expect(vm.FormError).toBe('Email already exists');
        });

        it('should set FormError for password1 error on signup error', function () {
            utilities.sendRequest = function (parameters, header) {
                parameters.callback.onError({
                    status: 400,
                    data: { password1: ['Password too short'] }
                });
            };
            vm.userSignUp(true);
            expect(vm.isFormError).toBe(true);
            expect(vm.FormError).toBe('Password too short');
        });

        it('should set FormError for password2 error on signup error', function () {
            utilities.sendRequest = function (parameters, header) {
                parameters.callback.onError({
                    status: 400,
                    data: { password2: ['Passwords do not match'] }
                });
            };
            vm.userSignUp(true);
            expect(vm.isFormError).toBe(true);
            expect(vm.FormError).toBe('Passwords do not match');
        });

        it('should notify on signup error exception', function () {
            utilities.sendRequest = function (parameters, header) {
                parameters.callback.onError({
                    status: 400,
                    data: null
                });
            };
            spyOn($rootScope, 'notify');
            vm.userSignUp(true);
            expect($rootScope.notify).toHaveBeenCalled();
        });





    });

    describe('Unit tests for setRefreshJWT function `accounts/user/get_auth_token`', function () {
        beforeEach(function () {
            spyOn(utilities, 'getData').and.returnValue('dummyUserKey');
        });

        it('should store refreshJWT on success', function () {
            spyOn(utilities, 'storeData');
            utilities.sendRequest = function (parameters, header) {
                expect(parameters.url).toBe('accounts/user/get_auth_token');
                expect(parameters.method).toBe('GET');
                expect(parameters.token).toBe('dummyUserKey');
                parameters.callback.onSuccess({ status: 200, data: { token: 'refreshToken' } });
            };
            vm.setRefreshJWT();
            expect(utilities.storeData).toHaveBeenCalledWith('refreshJWT', 'refreshToken');
        });

        it('should alert on non-200 status', function () {
            spyOn(window, 'alert');
            utilities.sendRequest = function (parameters, header) {
                parameters.callback.onSuccess({ status: 500 });
            };
            vm.setRefreshJWT();
            expect(window.alert).toHaveBeenCalledWith('Could not fetch Auth Token');
        });

        it('should handle 400 error with non_field_errors', function () {
            utilities.sendRequest = function (parameters, header) {
                parameters.callback.onError({ status: 400, data: { non_field_errors: ['Some error'] } });
            };
            vm.setRefreshJWT();
            expect(vm.isFormError).toBe(true);
            expect(vm.FormError).toBe('Some error');
        });

        it('should handle 400 error with exception', function () {
            spyOn($rootScope, 'notify');
            utilities.sendRequest = function (parameters, header) {
                parameters.callback.onError({ status: 400, data: null });
            };
            vm.setRefreshJWT();
            expect(vm.isFormError).toBe(true);
            expect($rootScope.notify).toHaveBeenCalled();
        });
    });


    describe('Unit tests for userLogin function `auth/login/`', function () {
        var nonFieldErrors, token;

        beforeEach(function () {
            nonFieldErrors = false;

            vm.getUser = {
                username: 'ford',
                password: 'dontpanic',
            };

            utilities.sendRequest = function (parameters) {
                var data, status, userKey;
                var error = 'error';
                var success = "success";
                var usernameRegex = /^[a-zA-Z0-9]+$/;
                var passwordRegex = /^[a-zA-Z0-9!@#$%^&*_]{8,30}$/;
                var isUsernameValid = usernameRegex.test(parameters.username);
                var isPasswordValid = passwordRegex.test(parameters.password);
                if (!isUsernameValid || !isPasswordValid) {
                    data = error;
                    status = 400;
                    userKey = "notFound";
                } else {
                    data = success;
                    status = 200;
                    userKey = "encrypted";
                }
                return {
                    "data": data,
                    "status": parseInt(status),
                    "userKey": userKey
                };
            };
        });

        it('correct login details', function () {
            vm.userLogin(true);
            var token = "encrypted";
            var response = utilities.sendRequest(vm.getUser);
            expect(response.status).toEqual(200);
            expect(response.data).toEqual("success");
            expect(angular.equals(response.userKey, token)).toEqual(true);
        });

        it('backend error', function () {
            vm.getUser.username = '';
            var token = "notFound";
            var response = utilities.sendRequest(vm.getUser);
            expect(response.status).toEqual(400);
            expect(response.data).toEqual("error");
            expect(angular.equals(response.userKey, token)).toEqual(true);
        });

        it('invalid details', function () {
            vm.userLogin(false);
            expect($rootScope.isLoader).toEqual(false);
        });

        it('should handle successful login and redirect to previousState', function () {
            spyOn(utilities, 'storeData');
            spyOn(vm, 'setRefreshJWT');
            spyOn($state, 'go');
            $rootScope.previousState = 'web.somewhere';
            utilities.sendRequest = function (parameters, header) {
                parameters.callback.onSuccess({ status: 200, data: { token: 'userToken' } });
            };
            vm.getUser = { name: 'ford', password: 'dontpanic' };
            vm.userLogin(true);
            expect(utilities.storeData).toHaveBeenCalledWith('userKey', 'userToken');
            expect(vm.setRefreshJWT).toHaveBeenCalled();
            expect($state.go).toHaveBeenCalledWith('web.somewhere');
        });

        it('should handle successful login and redirect to dashboard if no previousState', function () {
            spyOn(utilities, 'storeData');
            spyOn(vm, 'setRefreshJWT');
            spyOn($state, 'go');
            $rootScope.previousState = null;
            utilities.sendRequest = function (parameters, header) {
                parameters.callback.onSuccess({ status: 200, data: { token: 'userToken' } });
            };
            vm.getUser = { name: 'ford', password: 'dontpanic' };
            vm.userLogin(true);
            expect($state.go).toHaveBeenCalledWith('web.dashboard');
        });

        it('should alert on non-200 login response', function () {
            spyOn(window, 'alert');
            utilities.sendRequest = function (parameters, header) {
                parameters.callback.onSuccess({ status: 500 });
            };
            vm.userLogin(true);
            expect(window.alert).toHaveBeenCalledWith('Something went wrong');
        });

        it('should handle login error with non_field_errors', function () {
            utilities.sendRequest = function (parameters, header) {
                parameters.callback.onError({ status: 400, data: { non_field_errors: ['Login error'] } });
            };
            vm.userLogin(true);
            expect(vm.isFormError).toBe(true);
            expect(vm.FormError).toBe('Login error');
        });

        it('should handle login error with exception', function () {
            spyOn($rootScope, 'notify');
            utilities.sendRequest = function (parameters, header) {
                parameters.callback.onError({ status: 400, data: null });
            };
            vm.userLogin(true);
            expect(vm.isFormError).toBe(true);
            expect($rootScope.notify).toHaveBeenCalled();
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

        it('should set showPasswordStrength to true and update message/color when password is provided', function () {
            utilities.passwordStrength = function (password) {
                return ['Strong', 'green'];
            };
            vm.checkStrength('somePassword');
            expect(vm.showPasswordStrength).toBe(true);
            expect(vm.message).toBe('Strong');
            expect(vm.color).toBe('green');
        });

        it('should set showPasswordStrength to false and update message/color when password is empty', function () {
            utilities.passwordStrength = function (password) {
                return ['Weak', 'red'];
            };
            vm.checkStrength('');
            expect(vm.showPasswordStrength).toBe(false);
            expect(vm.message).toBe('Weak');
            expect(vm.color).toBe('red');
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

        it('should start loader and set correct parameters when verifyEmail is called', function () {
            spyOn(vm, 'startLoader');
            spyOn(utilities, 'sendRequest');
            $state.params.email_conf_key = 'abc123';
            vm.verifyEmail();
            expect(vm.startLoader).toHaveBeenCalledWith('Verifying Your Email');
            expect(utilities.sendRequest).toHaveBeenCalled();
            var params = utilities.sendRequest.calls.mostRecent().args[0];
            expect(params.url).toBe('auth/registration/account-confirm-email/abc123/');
            expect(params.method).toBe('GET');
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
                    parameters.callback.onError({ status: 400, data: { details: inactiveResponse } });
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

        it('should set FormError for expired/used token', function () {
            $state.params.user_id = 42;
            $state.params.reset_token = 'secure';
            utilities.sendRequest = function (parameters) {
                parameters.callback.onError({
                    data: {
                        token: ['Token is invalid or expired']
                    }
                });
            };
            vm.resetPasswordConfirm(true);
            expect(vm.isFormError).toBe(true);
            expect(vm.FormError).toBe('this link has been already used or expired.');
        });

        it('should set FormError for new_password1 error', function () {
            $state.params.user_id = 42;
            $state.params.reset_token = 'secure';
            utilities.sendRequest = function (parameters) {
                parameters.callback.onError({
                    data: {
                        new_password1: { error1: 'Too short', error2: 'No number' }
                    }
                });
            };
            vm.resetPasswordConfirm(true);
            expect(vm.isFormError).toBe(true);
            expect(vm.FormError).toContain('Too short');
            expect(vm.FormError).toContain('No number');
        });

        it('should set FormError for new_password2 error', function () {
            $state.params.user_id = 42;
            $state.params.reset_token = 'secure';
            utilities.sendRequest = function (parameters) {
                parameters.callback.onError({
                    data: {
                        new_password2: { error1: 'Passwords do not match' }
                    }
                });
            };
            vm.resetPasswordConfirm(true);
            expect(vm.isFormError).toBe(true);
            expect(vm.FormError).toContain('Passwords do not match');
        });
    });

    describe('Unit tests for checkPendingInvitation function', function () {
        beforeEach(function () {
            spyOn($window.sessionStorage, 'getItem');
            spyOn($window.sessionStorage, 'removeItem');
            spyOn($window.sessionStorage, 'setItem');
            spyOn($state, 'go');
        });

        it('should handle pending invitation redirect', function () {
            $window.sessionStorage.getItem.and.callFake(function(key) {
                if (key === 'pendingInvitationKey') return 'test-invitation-key';
                if (key === 'redirectAfterLogin') return 'web.challenge-host-team-invitation-accept';
                return null;
            });
            
            var result = vm.checkPendingInvitation();
            
            expect(result).toBe(true);
            expect($window.sessionStorage.removeItem).toHaveBeenCalledWith('redirectAfterLogin');
            expect($window.sessionStorage.setItem).toHaveBeenCalledWith('justCompletedLogin', 'true');
            expect($state.go).toHaveBeenCalledWith('web.challenge-host-team-invitation-accept', {
                invitation_key: 'test-invitation-key',
                justLoggedIn: true
            });
        });

        it('should return false when no pending invitation', function () {
            $window.sessionStorage.getItem.and.returnValue(null);
            
            var result = vm.checkPendingInvitation();
            
            expect(result).toBe(false);
            expect($state.go).not.toHaveBeenCalled();
        });

        it('should return false when redirectAfterLogin does not match', function () {
            $window.sessionStorage.getItem.and.callFake(function(key) {
                if (key === 'pendingInvitationKey') return 'test-invitation-key';
                if (key === 'redirectAfterLogin') return 'web.dashboard';
                return null;
            });
            
            var result = vm.checkPendingInvitation();
            
            expect(result).toBe(false);
            expect($state.go).not.toHaveBeenCalled();
        });

        it('should return false when no pendingInvitationKey', function () {
            $window.sessionStorage.getItem.and.callFake(function(key) {
                if (key === 'pendingInvitationKey') return null;
                if (key === 'redirectAfterLogin') return 'web.challenge-host-team-invitation-accept';
                return null;
            });
            
            var result = vm.checkPendingInvitation();
            
            expect(result).toBe(false);
            expect($state.go).not.toHaveBeenCalled();
        });
    });
});