'use strict';

describe('Unit tests for profile controller', function () {
    beforeEach(angular.mock.module('evalai'));

    var $controller, createController, $rootScope, $scope, utilities, $mdDialog, vm;

    beforeEach(inject(function (_$controller_, _$rootScope_, _utilities_, _$mdDialog_) {
        $controller = _$controller_;
        $rootScope = _$rootScope_;
        utilities = _utilities_;
        $mdDialog = _$mdDialog_;

        $scope = $rootScope.$new();
        createController = function () {
            return $controller('profileCtrl', {$scope: $scope});
        };
        vm = createController();
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
                    expect(vm.countLeft).toEqual(vm.countLeft + 1);
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
});
