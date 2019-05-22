'use strict';

describe('Unit tests for change password controller', function () {
    beforeEach(angular.mock.module('evalai'));
    
    var $controller, createController, $rootScope, $scope, utilities, $state, vm;
    
    beforeEach(inject(function (_$controller_, _$rootScope_, _utilities_, _$state_,) {
        $controller = _$controller_;
        $rootScope = _$rootScope_;
        utilities = _utilities_;
        $state = _$state_;

        $scope = $rootScope.$new();
        createController = function () {
            return $controller('ChangePwdCtrl', {$scope: $scope});
        };
        vm = createController();
    }));
    
    describe('Global variables', function () {
        it('has default values', function () {
            utilities.storeData('userKey', 'encrypted key');
            spyOn(utilities, 'getData');
            spyOn(angular, 'element');

            vm = createController();
            expect(utilities.getData).toHaveBeenCalledWith('userKey');
            expect(vm.wrnMsg).toEqual({});
            expect(vm.isValid).toEqual({});
            expect(vm.user).toEqual({});
            expect(vm.isFormError).toBeFalsy();
            expect($rootScope.canShowOldPassword).toBeFalsy();
            expect($rootScope.canShowNewPassword).toBeFalsy();
            expect($rootScope.canShowNewConfirmPassword).toBeFalsy();
            expect(angular.element).toHaveBeenCalledWith('.change-passowrd-card');
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

        it('toggleOldPasswordVisibility', function () {
            var canShowOldPassword = $rootScope.canShowOldPassword;
            vm.toggleOldPasswordVisibility();
            expect($rootScope.canShowOldPassword).toEqual(!canShowOldPassword);
        });

        it('toggleNewPasswordVisibility', function () {
            var canShowNewPassword = $rootScope.canShowOldPassword;
            vm.toggleNewPasswordVisibility();
            expect($rootScope.canShowNewPassword).toEqual(!canShowNewPassword);
        });

        it('toggleNewConfirmVisibility', function () {
            var canShowNewConfirmPassword = $rootScope.canShowOldPassword;
            vm.toggleNewConfirmVisibility();
            expect($rootScope.canShowNewConfirmPassword).toEqual(!canShowNewConfirmPassword);
        });
    });

    describe('Unit tests for changePassword function `auth/password/change/`', function () {
        var success;
        var try_response;
        
        beforeEach(function () {
            spyOn($rootScope, 'notify');
            spyOn(vm, 'startLoader');
            spyOn(vm, 'stopLoader');
            vm.user.old_password = "Old Password";
            vm.user.new_password1 = "New Password 1";
            vm.user.new_password2 = "New Password 2";

            utilities.sendRequest = function (parameters) {
                if (success) {
                    parameters.callback.onSuccess({
                        data: 'success'
                    });
                } else if (success == null){
                    parameters.callback.onError({
                        data: null
                    });
                } else {
                    parameters.callback.onError({
                        data: try_response
                    });
                }
            };
        });

        it('successfully change password', function () {
            var resetconfirmFormValid = true;
            success = true;
            $state.params.user_id = 1;

            vm.changePassword(resetconfirmFormValid);
            expect(vm.user.error).toBeFalsy();
            expect($rootScope.notify).toHaveBeenCalledWith("success", "Your password has been changed successfully!");
            expect(vm.stopLoader).toHaveBeenCalled();
        });

        it('when old password is valid', function () {
            var resetconfirmFormValid = true;
            success = false;
            $state.params.user_id = 1;
            try_response = {
                old_password: "old password"
            };

            vm.changePassword(resetconfirmFormValid);
            expect(vm.user.error).toEqual("Failed");
            expect(vm.isFormError).toBeTruthy();
            expect(vm.FormError).toEqual(Object.values(try_response.old_password).join(" "));
            expect(vm.stopLoader).toHaveBeenCalled();
        });

        it('when password1 is valid', function () {
            var resetconfirmFormValid = true;
            success = false;
            $state.params.user_id = 1;
            try_response = {
                new_password1: "password1"
            };

            vm.changePassword(resetconfirmFormValid);
            expect(vm.user.error).toEqual("Failed");
            expect(vm.isFormError).toBeTruthy();
            expect(vm.FormError).toEqual(Object.values(try_response.new_password1).join(" "));
            expect(vm.stopLoader).toHaveBeenCalled();
        });

        it('when password2 is valid', function () {
            var resetconfirmFormValid = true;
            success = false;
            $state.params.user_id = 1;
            try_response = {
                new_password2: "password2"
            };

            vm.changePassword(resetconfirmFormValid);
            expect(vm.user.error).toEqual("Failed");
            expect(vm.isFormError).toBeTruthy();
            expect(vm.FormError).toEqual(Object.values(try_response.new_password2).join(" "));
            expect(vm.stopLoader).toHaveBeenCalled();
        });

        it('backend error with catch clause', function () {
            var resetconfirmFormValid = true;
            success = null;
            $state.params.user_id = 1;

            vm.changePassword(resetconfirmFormValid);
            expect(vm.user.error).toEqual("Failed");
            expect(vm.isFormError).toBeTruthy();
            expect(vm.FormError).toEqual("Something went wrong! Please refresh the page and try again.");
            expect(vm.stopLoader).toHaveBeenCalled();
        });

        it('invalid form submission', function () {
            var resetconfirmFormValid = false;
            vm.changePassword(resetconfirmFormValid);
            expect(vm.stopLoader).toHaveBeenCalled();
        });
    });
});
