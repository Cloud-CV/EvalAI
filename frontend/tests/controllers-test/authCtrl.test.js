'use strict';

describe('Unit Tests for auth controller', function() {
    beforeEach(angular.mock.module('evalai'));

    var $controller, $rootScope, $state, $window, $scope, utilities, vm;

    beforeEach(inject(function(_$controller_, _$rootScope_, _$state_, _utilities_) {
        $controller = _$controller_;
        $rootScope = _$rootScope_;
        $state = _$state_;
        utilities = _utilities_;
        
        $scope = $rootScope.$new();
        vm = $controller('AuthCtrl', { $scope: $scope });
    }));

    describe('Global Variables', function() {
        it('has default values', function() {
            expect(vm.isRem).to.equal(false);
            expect(vm.isAuth).to.equal(false);
            expect(vm.isMail).to.equal(true);
            expect(vm.userMail).to.equal('');
            expect(vm.regUser).to.be.empty;
            expect(vm.getUser).to.be.empty;
            expect(vm.isResetPassword).to.equal(false);
            expect(vm.isFormError).to.equal(false);
            expect(vm.FormError).to.be.empty;
            expect(vm.redirectUrl).to.be.empty;
            expect(vm.isLoader).to.equal(false);
            expect(vm.isPassConf).to.equal(true);
            expect(vm.wrnMsg).to.be.empty;
            expect(vm.isValid).to.be.empty;
            expect(vm.confirmMsg).to.equal('');
            expect($rootScope.loaderTitle).to.equal('');
        });
    })

    describe('Validate helper functions', function() {
        it('startLoader', function() {
            var message = 'Start Loader';
            vm.startLoader(message);
            expect($rootScope.isLoader).to.equal(true);
            expect($rootScope.loaderTitle).to.equal(message);
        });

        it('stopLoader', function() {
            var message = '';
            vm.stopLoader();
            expect($rootScope.isLoader).to.equal(false);
            expect($rootScope.loaderTitle).to.equal(message);
        });

        it('resetForm', function() {
            vm.resetForm();
            expect(vm.regUser).to.be.empty;
            expect(vm.getUser).to.be.empty;
            expect(vm.wrnMsg).to.be.empty;
            expect(vm.isFormError).to.equal(false);
            expect(vm.isMail).to.equal(true);
        });
    });

    describe('Unit test for userSignUp function', function() {
        var errors = {
            username: 'username error',
            email: 'email error',
            password1: 'password error',
            password2: 'password confirm error'
        };

        beforeEach(function() {
            vm.regUser = {
                username: 'ford',
                email: 'fordprefect@hitchhikers.guide',
                password1: 'dontpanic',
                password2: 'dontpanic'
            };

            utilities.sendRequest = function(parameters) {
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
                }
            }
        });

        it('correct sign up details', function() {
            vm.userSignUp(true);
            var response = utilities.sendRequest(vm.regUser);
            expect(response.status).to.equal(201);
            expect(response.data).to.equal("success");
        });

        it('missing username', function() {
            vm.regUser.username = '';
            var response = utilities.sendRequest(vm.regUser);
            expect(response.status).to.equal(400);
            expect(response.data).to.equal(errors.username);
        });

        it('missing email', function() {
            vm.regUser.email = '';
            var response = utilities.sendRequest(vm.regUser);
            expect(response.status).to.equal(400);
            expect(response.data).to.equal(errors.email);
        });

        it('missing password', function() {
            vm.regUser.password1 = '';
            var response = utilities.sendRequest(vm.regUser);
            expect(response.status).to.equal(400);
            expect(response.data).to.equal(errors.password1);
        });

        it('mismatch password', function() {
            vm.regUser.password2 = 'failword';
            var response = utilities.sendRequest(vm.regUser);
            expect(response.status).to.equal(400);
            expect(response.data).to.equal(errors.password2);
        });

        it('invalid details', function() {
            vm.userSignUp(false);
            expect($rootScope.isLoader).to.equal(false);
        });
    });

    describe('Unit test for userLogin function', function() {
        var nonFieldErrors, token;
 
        beforeEach(function() {
            nonFieldErrors = false;

            vm.getUser = {
                username: 'ford',
                password: 'dontpanic',
            };

            utilities.sendRequest = function(parameters) {
                var data, status, userKey;
                var error = 'error';
                var success = "success"
                var usernameRegex = /^[a-zA-Z0-9]+$/;
                var passwordRegex = /^[a-zA-Z0-9!@#$%^&*_]{8,30}$/;
                var isUsernameValid = usernameRegex.test(parameters.username);
                var isPasswordValid = passwordRegex.test(parameters.password);
                if (!isUsernameValid || !isPasswordValid) {
                    data = error;
                    status = 400;
                    userKey = "notFound";
                }
                else {
                    data = success;
                    status = 200;
                    userKey = "encrypted";
                }
                return {
                    "data": data,
                    "status": parseInt(status),
                    "userKey": userKey
                }
            };
        });

        it('correct login details', function() {
            vm.userLogin(true);
            var token = "encrypted";
            var response = utilities.sendRequest(vm.getUser);
            expect(response.status).to.equal(200);
            expect(response.data).to.equal("success");
            expect(angular.equals(response.userKey, token)).to.equal(true);
        });

        it('backend error', function() {
            vm.getUser.username = '';
            var token = "notFound";
            var response = utilities.sendRequest(vm.getUser);
            expect(response.status).to.equal(400);
            expect(response.data).to.equal("error");
            expect(angular.equals(response.userKey, token)).to.equal(true);
        });

        it('invalid details', function() {
            vm.userLogin(false);
            expect($rootScope.isLoader).to.equal(false);
        });
    });

    describe('verifyEmail', function() {
        var verified;

        beforeEach(function() {
            utilities.sendRequest = function(parameters) {
                if (verified) {
                    parameters.callback.onSuccess();
                } else {
                    parameters.callback.onError();
                }
            };
        });

        it('correct email', function() {
            verified = true;
            vm.verifyEmail();
            expect(vm.email_verify_msg).to.equal('Your email has been verified successfully');
        });

        it('incorrect email', function() {
            verified = false;
            vm.verifyEmail();
            expect(vm.email_verify_msg).to.equal('Something went wrong!! Please try again.');
        });
    });

    describe('resetPassword', function() {
        var success;

        var mailSent = 'mail sent';

        beforeEach(function() {
            utilities.sendRequest = function(parameters) {
                if (success) {
                    parameters.callback.onSuccess({
                        data: {
                            success: mailSent
                        }
                    });
                } else {
                    parameters.callback.onError();
                }
            };
        });

        it('sent successfully', function() {
            success = true;
            vm.resetPassword(true);
            expect(vm.isFormError).to.equal(false);
            expect(vm.deliveredMsg).to.equal(mailSent);
        });

        it('backend error', function() {
            success = false;
            vm.resetPassword(true);
            expect(vm.isFormError).to.equal(true);
        });

        it('invalid details', function() {
            vm.resetPassword(false);
            expect($rootScope.isLoader).to.equal(false);
        });
    });

    describe('resetPasswordConfirm', function() {
        var success;

        var resetConfirm = 'password reset confirmed';

        beforeEach(function() {
            utilities.sendRequest = function(parameters) {
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

        it('successful reset', function() {
            $state.params.user_id = 42;
            $state.params.reset_token = 'secure';
            success = true;
            vm.resetPasswordConfirm(true);
            expect(vm.isResetPassword).to.equal(true);
            expect(vm.deliveredMsg).to.equal(resetConfirm);
        });

        it('backend error', function() {
            $state.params.user_id = 42;
            success = false;
            vm.resetPasswordConfirm(true);
            expect(vm.isFormError).to.equal(true);
        });

        it('invalid details', function() {
            vm.resetPasswordConfirm(false);
            expect($rootScope.isLoader).to.equal(false);
        });
    });
});
