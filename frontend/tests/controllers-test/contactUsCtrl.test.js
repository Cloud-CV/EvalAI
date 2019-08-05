'use strict';

describe('Unit tests for ContactUs Controller', function () {
    beforeEach(angular.mock.module('evalai'));

    var $controller, createController, $rootScope, $scope, utilities, $state, vm;

    beforeEach(inject(function (_$controller_, _$rootScope_, _utilities_, _$state_,) {
        $controller = _$controller_;
        $rootScope = _$rootScope_;
        utilities = _utilities_;
        $state = _$state_;

        $scope = $rootScope.$new();
        createController = function () {
            return $controller('contactUsCtrl', {$scope: $scope});
        };
        vm = $controller('contactUsCtrl', { $scope: $scope });
    }));

    describe('Global variables', function () {
        it('has default values', function () {
            utilities.storeData('userKey', 'encrypted key');
            spyOn(utilities, 'getData');
            vm = createController();
            expect(utilities.getData).toHaveBeenCalledWith('userKey');
            expect(vm.wrnMsg).toEqual({});
            expect(vm.isValid).toEqual({});
            expect(vm.user).toEqual({});
            expect(vm.isFormError).toBeFalsy();
        });
    });

    describe('Unit tests for global backend call', function () {
        var success;
        var successResponse = {
            name: "Some Name",
            email: "abc@gmail.com"
        };
        var errorResponse = 'error';

        beforeEach(function (){
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

        it('get the previous profile data `web/contact/`', function () {
            success = true;
            vm = createController();
            expect(vm.user).toEqual(successResponse);
            expect(vm.isDisabled).toBeTruthy();
        });
    });

    describe('Unit tests for contactUs function `web/contact/`', function () {
        var success, tryClauseResponse = {};
        var successResponse = {
            message: "Some Message",
        };
        var usernameInvalid  = {
            name: ["xyz"],
        };
        var emailInvalid = {
            email: ["xyz@gmail.com"],
        };
        var messageInvalid = {
            message: ["New Message"]
        };

        beforeEach(function () {
            spyOn($rootScope, 'notify');
            spyOn(vm, 'startLoader');
            spyOn(vm, 'stopLoader');
            spyOn($state, 'go');

            utilities.sendRequest = function (parameters) {
                if (success) {
                    parameters.callback.onSuccess({
                        data: successResponse,
                        status: 201
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

        it('successfully post data in contact us form', function () {
            var resetconfirmFormValid = true;
            success = true;
            vm.user.name = "abc";
            vm.user.email = "abc@gmail.com";
            vm.user.message = "Some Other Message";

            vm.contactUs(resetconfirmFormValid);
            expect(vm.isDisabled).toBeFalsy();
            expect($rootScope.notify).toHaveBeenCalledWith("success", successResponse.message);
            expect($state.go).toHaveBeenCalledWith('home');
            expect(vm.stopLoader).toHaveBeenCalled();
        });

        it('when username is invalid', function () {
            var resetconfirmFormValid = true;
            tryClauseResponse = usernameInvalid;
            success = false;
            vm.user.name = "abc";
            vm.user.email = "abc@gmail.com";
            vm.user.message = "Some Other Message";

            vm.contactUs(resetconfirmFormValid);
            expect(vm.isDisabled).toBeFalsy();
            expect(vm.isFormError).toBeTruthy();
            expect(vm.FormError).toEqual(tryClauseResponse.name[0]);
            expect(vm.stopLoader).toHaveBeenCalled();
        });

        it('when email is invalid', function () {
            var resetconfirmFormValid = true;
            tryClauseResponse = emailInvalid;
            success = false;
            vm.user.name = "abc";
            vm.user.email = "abc@gmail.com";
            vm.user.message = "Some Other Message";

            vm.contactUs(resetconfirmFormValid);
            expect(vm.isDisabled).toBeFalsy();
            expect(vm.isFormError).toBeTruthy();
            expect(vm.FormError).toEqual(tryClauseResponse.email[0]);
            expect(vm.stopLoader).toHaveBeenCalled();
        });

        it('when message is invalid', function () {
            var resetconfirmFormValid = true;
            tryClauseResponse = messageInvalid;
            success = false;
            vm.user.name = "abc";
            vm.user.email = "abc@gmail.com";
            vm.user.message = "Some Other Message";

            vm.contactUs(resetconfirmFormValid);
            expect(vm.isDisabled).toBeFalsy();
            expect(vm.isFormError).toBeTruthy();
            expect(vm.FormError).toEqual(tryClauseResponse.message[0]);
            expect(vm.stopLoader).toHaveBeenCalled();
        });

        it('other backend error in try clause', function () {
            var resetconfirmFormValid = true;
            tryClauseResponse = {};
            success = false;
            vm.user.name = "abc";
            vm.user.email = "abc@gmail.com";
            vm.user.message = "Some Other Message";

            vm.contactUs(resetconfirmFormValid);
            expect(vm.isDisabled).toBeFalsy();
            expect(vm.isFormError).toBeTruthy();
            expect($rootScope.notify).toHaveBeenCalledWith("error", "Some error occured. Please try again!");
            expect(vm.stopLoader).toHaveBeenCalled();
        });

        it('backend error with catch clause', function () {
            var resetconfirmFormValid = true;
            success = null;
            vm.user.name = "abc";
            vm.user.email = "abc@gmail.com";
            vm.user.message = "Some Other Message";

            vm.contactUs(resetconfirmFormValid);
            expect(vm.isDisabled).toBeFalsy();
            expect($rootScope.notify).toHaveBeenCalled();
            expect(vm.stopLoader).toHaveBeenCalled();
        });
    });
});
