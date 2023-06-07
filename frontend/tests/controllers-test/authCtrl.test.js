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
});
