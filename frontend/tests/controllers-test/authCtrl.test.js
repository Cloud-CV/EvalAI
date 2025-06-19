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
    });


        describe('togglePasswordVisibility function', function() {
        it('should toggle password visibility to true when false', function() {
            $rootScope.canShowPassword = false;
            vm.togglePasswordVisibility();
            expect($rootScope.canShowPassword).toEqual(true);
        });

        it('should toggle password visibility to false when true', function() {
            $rootScope.canShowPassword = true;
            vm.togglePasswordVisibility();
            expect($rootScope.canShowPassword).toEqual(false);
        });
    });

    // Test 2: Missing toggleConfirmPasswordVisibility function
    describe('toggleConfirmPasswordVisibility function', function() {
        it('should toggle confirm password visibility to true when false', function() {
            $rootScope.canShowConfirmPassword = false;
            vm.toggleConfirmPasswordVisibility();
            expect($rootScope.canShowConfirmPassword).toEqual(true);
        });

        it('should toggle confirm password visibility to false when true', function() {
            $rootScope.canShowConfirmPassword = true;
            vm.toggleConfirmPasswordVisibility();
            expect($rootScope.canShowConfirmPassword).toEqual(false);
        });
    });

    describe('checkPendingInvitation function', function() {
        beforeEach(function() {
            spyOn($state, 'go');
        });

        it('should handle pending invitation redirect successfully', function() {
            $window.sessionStorage.getItem.and.callFake(function(key) {
                if (key === 'pendingInvitationKey') return 'test-invitation-key';
                if (key === 'redirectAfterLogin') return 'web.challenge-host-team-invitation-accept';
                return null;
            });

            var result = vm.checkPendingInvitation();

            expect($window.sessionStorage.removeItem).toHaveBeenCalledWith('redirectAfterLogin');
            expect($window.sessionStorage.setItem).toHaveBeenCalledWith('justCompletedLogin', 'true');
            expect($state.go).toHaveBeenCalledWith('web.challenge-host-team-invitation-accept', {
                invitation_key: 'test-invitation-key',
                justLoggedIn: true
            });
            expect(result).toEqual(true);
        });

        it('should return false when no pending invitation exists', function() {
            $window.sessionStorage.getItem.and.returnValue(null);

            var result = vm.checkPendingInvitation();

            expect(result).toEqual(false);
            expect($state.go).not.toHaveBeenCalled();
        });

        it('should return false when only invitation key exists without redirect flag', function() {
            $window.sessionStorage.getItem.and.callFake(function(key) {
                if (key === 'pendingInvitationKey') return 'test-invitation-key';
                return null;
            });

            var result = vm.checkPendingInvitation();

            expect(result).toEqual(false);
        });
    });

    describe('setRefreshJWT function', function() {
        beforeEach(function() {
            spyOn(utilities, 'getData').and.returnValue('mock-user-key');
            spyOn(utilities, 'storeData');
            spyOn(utilities, 'sendRequest');
        });

        it('should successfully fetch and store refresh JWT', function() {
            utilities.sendRequest.and.callFake(function(parameters) {
                parameters.callback.onSuccess({
                    status: 200,
                    data: { token: 'mock-refresh-token' }
                });
            });

            vm.setRefreshJWT();

            expect(utilities.sendRequest).toHaveBeenCalledWith(jasmine.objectContaining({
                url: 'accounts/user/get_auth_token',
                method: 'GET',
                token: 'mock-user-key'
            }), "header");
            expect(utilities.storeData).toHaveBeenCalledWith('refreshJWT', 'mock-refresh-token');
        });

        it('should handle non-200 response with alert', function() {
            spyOn(window, 'alert');
            utilities.sendRequest.and.callFake(function(parameters) {
                parameters.callback.onSuccess({
                    status: 400,
                    data: { token: 'mock-refresh-token' }
                });
            });

            vm.setRefreshJWT();

            expect(window.alert).toHaveBeenCalledWith("Could not fetch Auth Token");
            expect(utilities.storeData).not.toHaveBeenCalled();
        });

        it('should handle error response with non_field_errors', function() {
            utilities.sendRequest.and.callFake(function(parameters) {
                parameters.callback.onError({
                    status: 400,
                    data: { non_field_errors: ['Token fetch failed'] }
                });
            });

            vm.setRefreshJWT();

            expect(vm.isFormError).toEqual(true);
            expect(vm.FormError).toEqual('Token fetch failed');
        });

        it('should handle error response without non_field_errors', function() {
            spyOn($rootScope, 'notify');
            utilities.sendRequest.and.callFake(function(parameters) {
                parameters.callback.onError({
                    status: 400,
                    data: { other_error: 'Some other error' }
                });
            });

            vm.setRefreshJWT();

            expect(vm.isFormError).toEqual(true);
            expect(vm.FormError).toEqual({});
        });

        it('should handle exception in error callback', function() {
            spyOn($rootScope, 'notify');
            utilities.sendRequest.and.callFake(function(parameters) {
                parameters.callback.onError({
                    status: 400,
                    data: null
                });
            });

            vm.setRefreshJWT();

            expect($rootScope.notify).toHaveBeenCalledWith("error", jasmine.any(Error));
        });
    });

    describe('checkStrength function', function() {
        beforeEach(function() {
            spyOn(utilities, 'passwordStrength').and.returnValue(['Strong', 'green']);
        });

        it('should show password strength when password provided', function() {
            vm.checkStrength('testpassword123');

            expect(vm.showPasswordStrength).toEqual(true);
            expect(utilities.passwordStrength).toHaveBeenCalledWith('testpassword123');
            expect(vm.message).toEqual('Strong');
            expect(vm.color).toEqual('green');
        });

        it('should hide password strength when no password provided', function() {
            vm.checkStrength('');

            expect(vm.showPasswordStrength).toEqual(false);
            expect(utilities.passwordStrength).toHaveBeenCalledWith('');
        });

        it('should hide password strength when null password provided', function() {
            vm.checkStrength(null);

            expect(vm.showPasswordStrength).toEqual(false);
        });

        it('should hide password strength when undefined password provided', function() {
            vm.checkStrength(undefined);

            expect(vm.showPasswordStrength).toEqual(false);
        });
    });

    // Test 6: Missing $stateChangeStart event handler
    describe('$stateChangeStart event handler', function() {
        it('should call resetForm on state change', function() {
            spyOn(vm, 'resetForm');

            $rootScope.$broadcast('$stateChangeStart');

            expect(vm.resetForm).toHaveBeenCalled();
        });
    });

    // Test 7: Missing coverage in userSignUp function
    describe('Additional userSignUp coverage', function() {
        beforeEach(function() {
            vm.regUser = {
                name: 'ford',
                email: 'fordprefect@hitchhikers.guide',
                password: 'dontpanic',
                confirm_password: 'dontpanic'
            };
        });

        it('should handle successful signup but non-200 login response', function() {
            spyOn(window, 'alert');
            utilities.sendRequest = function(parameters) {
                if (parameters.url === 'auth/registration/') {
                    parameters.callback.onSuccess({ status: 201 });
                } else if (parameters.url === 'auth/login/') {
                    parameters.callback.onSuccess({ status: 400 });
                }
            };

            vm.userSignUp(true);

            expect(window.alert).toHaveBeenCalledWith("Something went wrong");
        });

        it('should handle login error after successful signup', function() {
            utilities.sendRequest = function(parameters) {
                if (parameters.url === 'auth/registration/') {
                    parameters.callback.onSuccess({ status: 201 });
                } else if (parameters.url === 'auth/login/') {
                    parameters.callback.onError({
                        status: 400,
                        data: { non_field_errors: ['Login failed'] }
                    });
                }
            };

            vm.userSignUp(true);

            expect(vm.isFormError).toEqual(true);
            expect(vm.FormError).toEqual('Login failed');
        });

        it('should handle login exception after successful signup', function() {
            spyOn($rootScope, 'notify');
            utilities.sendRequest = function(parameters) {
                if (parameters.url === 'auth/registration/') {
                    parameters.callback.onSuccess({ status: 201 });
                } else if (parameters.url === 'auth/login/') {
                    parameters.callback.onError({
                        status: 400,
                        data: null
                    });
                }
            };

            vm.userSignUp(true);

            expect($rootScope.notify).toHaveBeenCalledWith("error", jasmine.any(Error));
        });
    });

    // Test 8: Missing coverage in userLogin function  
    describe('Additional userLogin coverage', function() {
        beforeEach(function() {
            vm.getUser = {
                name: 'ford',
                password: 'dontpanic'
            };
            spyOn(vm, 'setRefreshJWT');
            spyOn(vm, 'checkPendingInvitation').and.returnValue(false);
            spyOn($state, 'go');
        });

        it('should handle successful login with previous state redirect', function() {
            $rootScope.previousState = 'web.previous-page';
            utilities.sendRequest = function(parameters) {
                parameters.callback.onSuccess({
                    status: 200,
                    data: { token: 'user-token' }
                });
            };

            vm.userLogin(true);

            expect($state.go).toHaveBeenCalledWith('web.previous-page');
        });

        it('should handle successful login with pending invitation', function() {
            vm.checkPendingInvitation.and.returnValue(true);
            utilities.sendRequest = function(parameters) {
                parameters.callback.onSuccess({
                    status: 200,
                    data: { token: 'user-token' }
                });
            };

            vm.userLogin(true);

            expect(vm.checkPendingInvitation).toHaveBeenCalled();
            expect($state.go).not.toHaveBeenCalledWith('web.dashboard');
        });

        it('should handle login exception in error callback', function() {
            spyOn($rootScope, 'notify');
            utilities.sendRequest = function(parameters) {
                parameters.callback.onError({
                    status: 400,
                    data: null
                });
            };

            vm.userLogin(true);

            expect($rootScope.notify).toHaveBeenCalledWith("error", jasmine.any(Error));
        });
    });
});
