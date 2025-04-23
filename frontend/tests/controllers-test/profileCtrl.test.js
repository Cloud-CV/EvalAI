'use strict';

describe('Unit tests for profile controller', function () {
    beforeEach(angular.mock.module('evalai'));

    var $controller, createController, $rootScope, $scope, utilities, $mdDialog, $state, vm;

    beforeEach(inject(function (_$controller_, _$rootScope_, _utilities_, _$mdDialog_, _$state_) {
        $controller = _$controller_;
        $rootScope = _$rootScope_;
        utilities = _utilities_;
        $mdDialog = _$mdDialog_;
        $state = _$state_;

        $scope = $rootScope.$new();
        createController = function () {
            return $controller('profileCtrl', {$scope: $scope});
        };
        vm = $controller('profileCtrl', { $scope: $scope });
    }));

    describe('Global variables', function () {
        beforeEach(function () {
            spyOn(utilities, 'hideLoader');
            spyOn(utilities, 'storeData');
            spyOn(utilities, 'getData');
        });

        it('has default values', function () {	
            vm = createController();
            expect(vm.user).toEqual({});
            expect(vm.countLeft).toEqual(0);
            expect(vm.compPerc).toEqual(0);
            expect(vm.inputType).toEqual('password');
            expect(vm.status).toEqual('Show');
            expect(vm.token).toEqual('');

            expect(utilities.hideLoader).toHaveBeenCalled()
            expect(vm.imgUrlObj).toEqual({profilePic: "dist/images/spaceman.png"});
            expect(utilities.getData).toHaveBeenCalledWith('userKey');
        });
    });

    describe('Unit tests for global backend call', function () {
        var success, successResponse;
        var response = ["", null, "abc", undefined, "xyz"];
        var errorResponse = {
            error: 'error'
        };

        beforeEach(function () {
            utilities.sendRequest = function (parameters) {
                if (success) {
                    parameters.callback.onSuccess({
                        data: successResponse,
                        status: 200
                    });
                } else {
                    parameters.callback.onError({
                        data: errorResponse
                    });
                }
            };
        });

        it('getting the user profile details `auth/user/`', function () {
            success = true;
            successResponse = response;
            var count = 0;
            vm = createController();
            for (var i = 0; i < successResponse.length; i++) {
                if (successResponse[i] === "" || successResponse[i] === undefined || successResponse[i] === null) {
                    successResponse[i] = "-";
                    expect(vm.countLeft).toEqual(vm.countLeft);
                }
                count = count + 1;
            }
            expect(vm.compPerc).toEqual(parseInt((vm.countLeft / count) * 100));
            expect(vm.user).toEqual(successResponse);
            expect(vm.user.complete).toEqual(100 - vm.compPerc);
        });

        it('backend error on getting profile details `auth/user/`', function () {
            success = false;
            spyOn($rootScope, 'notify');
            vm = createController();
            expect($rootScope.notify).toHaveBeenCalledWith("error", errorResponse.error);
        });

        it('get auth token `accounts/user/get_auth_token`', function () {
            success = true;
            successResponse = {
                token: 'abcdef01234'
            };
            vm = createController();
            expect(vm.jsonResponse).toEqual(successResponse);
            expect(vm.token).toEqual(successResponse.token);
        });

        it('backend error on getting auth token `accounts/user/get_auth_token`', function () {
            success = false;
            errorResponse = {
                detail: 'error'
            };
            spyOn($rootScope, 'notify');
            vm = createController();
            expect($rootScope.notify).toHaveBeenCalledWith("error", errorResponse.detail);
        });
    });

    describe('Unit tests for hideShowPassword function', function () {
        it('when input type is `password`', function () {
            vm.inputType = 'password';
            vm.hideShowPassword();
            expect(vm.inputType).toEqual('text');
            expect(vm.status).toEqual('Hide');
        });

        it('when input type is `text`', function () {
            vm.inputType = 'text';
            vm.hideShowPassword();
            expect(vm.inputType).toEqual('password');
            expect(vm.status).toEqual('Show');
        });
    });

    describe('Unit tests for showConfirmation function', function () {
        beforeEach(function () {
            spyOn($rootScope, 'notify');
        });

        it('successfully token copied to clipboard', function () {
            vm.showConfirmation();
            expect($rootScope.notify).toHaveBeenCalledWith("success", "Token copied to your clipboard.");
        });
    });

    describe('Unit tests for getAuthTokenDialog function', function () {
        it('open token dialog', function () {
            var $mdDialogOpened = false;
            spyOn($mdDialog, 'show').and.callFake(function () {
                $mdDialogOpened = true;
            });

            vm.getAuthTokenDialog();
            expect(vm.titleInput).toEqual("");
            expect($mdDialog.show).toHaveBeenCalled();
            expect($mdDialogOpened).toBeTruthy();
        });
    });

    describe('Unit tests for getAuthToken function', function () {
        beforeEach(function () {
            spyOn($mdDialog, 'hide');
        });

        it('successfully set input type to `password`', function () {
            var getTokenForm = false;
            vm.getAuthToken(getTokenForm);
            expect(vm.inputType).toEqual('password');
            expect(vm.status).toEqual('Show');
            expect($mdDialog.hide).toHaveBeenCalled();
        });
    });

    describe('Unit tests for `updateProfile` function', function () {
        var success, tryClauseResponse;
        var usernameInvalid  = {
            username: ["username error"],
        };
        var firstnameInvalid = {
            first_name: ["firstname error"],
        };
        var lastnameInvalid = {
            last_name: ["lastname error"]
        };
        var affiliationInvalid = {
            affiliation: ["affiliation error"]
        };

        beforeEach(function () {
            spyOn($rootScope, 'notify');
            spyOn($state, 'go');
            spyOn($state, 'reload');
            vm.user.first_name = "firstname";
            vm.user.last_name = "lastname";
            vm.user.affiliation = "affiliation";

            utilities.sendRequest = function (parameters) {
                if (success) {
                    parameters.callback.onSuccess({
                        data: 'success',
                        status: 200
                    });
                } else if (success == null){
                    parameters.callback.onError({
                        data: null,
                        status: 400
                    });
                } else {
                    parameters.callback.onError({
                        data: tryClauseResponse,
                        status: 400
                    });
                }
            };
        });

        it('successfully updated profile', function () {
            var resetconfirmFormValid = true;
            success = true;
            vm.updateProfile(resetconfirmFormValid);
            expect($rootScope.notify).toHaveBeenCalledWith("success", "Profile updated successfully!");
            expect($state.reload());
            $mdDialog.hide();
        });

        it('when firstname is invalid', function () {
            var resetconfirmFormValid = true;
            tryClauseResponse = firstnameInvalid;
            success = false;

            vm.updateProfile(resetconfirmFormValid);
            expect(vm.isFormError).toBeTruthy();
            expect(vm.FormError).toEqual(tryClauseResponse.first_name[0]);
        });

        it('when lastname is invalid', function () {
            var resetconfirmFormValid = true;
            tryClauseResponse = lastnameInvalid;
            success = false;

            vm.updateProfile(resetconfirmFormValid);
            expect(vm.isFormError).toBeTruthy();
            expect(vm.FormError).toEqual(tryClauseResponse.last_name[0]);
        });

        it('when affiliation is invalid', function () {
            var resetconfirmFormValid = true;
            tryClauseResponse = affiliationInvalid;
            success = false;

            vm.updateProfile(resetconfirmFormValid);
            expect(vm.isFormError).toBeTruthy();
            expect(vm.FormError).toEqual(tryClauseResponse.affiliation[0]);
        });

        it('other backend error in try clause', function () {
            var resetconfirmFormValid = true;
            tryClauseResponse = {};
            success = false;

            vm.updateProfile(resetconfirmFormValid);
            expect(vm.isDisabled).toBeFalsy();
            expect(vm.isFormError).toBeTruthy();
            expect($rootScope.notify).toHaveBeenCalledWith("error", "Some error have occured . Please try again !");
        });

        it('backend error with catch clause', function () {
            var resetconfirmFormValid = true;
            success = null;

            vm.updateProfile(resetconfirmFormValid);
            expect(vm.isDisabled).toBeFalsy();
            expect($rootScope.notify).toHaveBeenCalled();
        });

        it('invalid form submission', function () {
            var resetconfirmFormValid = false;
            vm.updateProfile(resetconfirmFormValid);
            $mdDialog.hide();
            $state.reload();
        });
    });

    describe('Unit tests for `deactivate user` function', function () {
        var success, deactivateAccountForm;
        var errorResponse = {
            error: 'error'
        };

        beforeEach(function () {
            spyOn($rootScope, 'notify');
            spyOn($state, 'go');

            utilities.sendRequest = function (parameters) {
                if (success) {
                    parameters.callback.onSuccess({
                        data: 'success',
                        status: 200
                    });
                } else {
                    parameters.callback.onError({
                        data: errorResponse,
                        status: 400
                    });
                }
            };
        });

        it('successfully deactivated user', function () {
            success = true;
            deactivateAccountForm = true;
            vm.confirmDeactivateAccount(deactivateAccountForm);
            expect($rootScope.notify).toHaveBeenCalledWith("success", "Your account has been deactivated successfully.");
            expect($state.go).toHaveBeenCalledWith("home");
        });

        it('backend error', function () {
            success = false;
            deactivateAccountForm = true;
            vm.confirmDeactivateAccount(deactivateAccountForm);
            expect($rootScope.notify).toHaveBeenCalledWith("error", errorResponse.error);
        });
    });

    describe('Unit tests for isURLValid function', function () {
        it('should allow empty URLs', function () {
            var result = vm.isURLValid('');
            expect(result).toBeTruthy();
    
            result = vm.isURLValid(null);
            expect(result).toBeTruthy();
    
            result = vm.isURLValid(undefined);
            expect(result).toBeTruthy();
        });
    
        it('should return true for valid URLs within 200 characters', function () {
            var result = vm.isURLValid('https://github.com');
            expect(result).toBeTruthy();
    
            result = vm.isURLValid('http://example.com/path?query=param');
            expect(result).toBeTruthy();
    
            result = vm.isURLValid('https://sub.domain.example.com/long-path/to/resource?query=1&more=2');
            expect(result).toBeTruthy();
        });
    
        it('should return false for invalid URLs or overly long ones', function () {
            var result = vm.isURLValid('invalid-url');
            expect(result).toBeFalsy();
    
            result = vm.isURLValid('htp://missing-schema.com');
            expect(result).toBeFalsy();
    
            var longUrl = 'http://example.com/' + 'a'.repeat(201);
            result = vm.isURLValid(longUrl);
            expect(result).toBeFalsy();
        });
    });
  
    describe('Unit tests for showTokenExpiredDialog function', function () {
        beforeEach(function () {
            spyOn($mdDialog, 'show').and.callFake(function (options) {
                var fakeScope = $rootScope.$new();

                var controllerFn = Array.isArray(options.controller)
                    ? options.controller[options.controller.length - 1]
                    : options.controller;

                controllerFn(fakeScope, $mdDialog);

                expect(typeof fakeScope.refreshToken).toBe('function');
                expect(typeof fakeScope.dismiss).toBe('function');

                return {
                    then: function (confirmCallback, cancelCallback) {
                        if (confirmCallback) confirmCallback();
                    }
                };
            });

            spyOn(vm, 'refreshToken'); // Spy on refreshToken to ensure it gets called
        });

        it('should open token expired dialog with correct config and call refreshToken', function () {
            vm.showTokenExpiredDialog();

            expect($mdDialog.show).toHaveBeenCalled();

            var dialogArgs = $mdDialog.show.calls.mostRecent().args[0];
            expect(dialogArgs.templateUrl).toBe('dist/views/web/auth/token-expired-dialog.html');

            var testScope = $rootScope.$new();
            var controllerFn = Array.isArray(dialogArgs.controller)
                ? dialogArgs.controller[dialogArgs.controller.length - 1]
                : dialogArgs.controller;

            controllerFn(testScope, $mdDialog);
            testScope.refreshToken();

            expect(vm.refreshToken).toHaveBeenCalled();
        });
    });
});
