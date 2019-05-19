'use strict';

describe('Unit tests for ContactUs Controller', function () {
	beforeEach(angular.mock.module('evalai'));

	var $controller, createController, $rootScope, $scope, utilities, $state, vm;

	beforeEach(inject(function(_$controller_, _$rootScope_, _utilities_, _$state_,) {
		$controller = _$controller_;
        $rootScope = _$rootScope_;
        utilities = _utilities_;
        $state = _$state_;

        $scope = $rootScope.$new();
        createController = function () {
            return $controller('contactUsCtrl', { $scope: $scope });
        };
        vm = createController();
	}));

	describe('Global variables', function() {
		it('has default values', function() {
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
        var success_response = {
            name: "Some Name",
            email: "abc@gmail.com"
        };
        var error_response = 'error';

        beforeEach(function (){
            utilities.sendRequest = function (parameters) {
                if (success) {
                    parameters.callback.onSuccess({
                        data: success_response,
                        status: 200
                    });
                } else {
                    parameters.callback.onError({
                        data: error_response
                    });
                }
            };
        });

        it('get the previous profile data `web/contact/`', function () {
            success = true;
            vm = createController();
            expect(vm.user).toEqual(success_response);
            expect(vm.isDisabled).toBeTruthy();
        });
    });

	describe('Unit tests for contactUs function `web/contact/`', function () {
    	var success, try_response = {};
        var success_response = {
            message: "Some Message",
        };
        var username_valid  = {
        	name: ["xyz"],
        };
        var email_valid = {
        	email: ["xyz@gmail.com"],
        };
        var message_valid = {
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
                        data: success_response,
                        status: 201
                    });
                } else if (success == null){
                    parameters.callback.onError({
                        data: null,
                        status: 400
                    });
                } else {
                    parameters.callback.onError({
                        data: try_response,
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
        	expect($rootScope.notify).toHaveBeenCalledWith("success", success_response.message);
        	expect($state.go).toHaveBeenCalledWith('home');
        	expect(vm.stopLoader).toHaveBeenCalled();
        });

        it('when username is valid', function () {
        	var resetconfirmFormValid = true;
        	try_response = username_valid;
        	success = false;
        	vm.user.name = "abc";
        	vm.user.email = "abc@gmail.com";
        	vm.user.message = "Some Other Message";

        	vm.contactUs(resetconfirmFormValid);
        	expect(vm.isDisabled).toBeFalsy();
        	expect(vm.isFormError).toBeTruthy();
        	expect(vm.FormError).toEqual(try_response.name[0]);
        	expect(vm.stopLoader).toHaveBeenCalled();
        });

        it('when email is valid', function () {
        	var resetconfirmFormValid = true;
        	try_response = email_valid;
        	success = false;
        	vm.user.name = "abc";
        	vm.user.email = "abc@gmail.com";
        	vm.user.message = "Some Other Message";

        	vm.contactUs(resetconfirmFormValid);
        	expect(vm.isDisabled).toBeFalsy();
        	expect(vm.isFormError).toBeTruthy();
        	expect(vm.FormError).toEqual(try_response.email[0]);
        	expect(vm.stopLoader).toHaveBeenCalled();
        });

        it('when message is valid', function () {
        	var resetconfirmFormValid = true;
        	try_response = message_valid;
        	success = false;
        	vm.user.name = "abc";
        	vm.user.email = "abc@gmail.com";
        	vm.user.message = "Some Other Message";

        	vm.contactUs(resetconfirmFormValid);
        	expect(vm.isDisabled).toBeFalsy();
        	expect(vm.isFormError).toBeTruthy();
        	expect(vm.FormError).toEqual(try_response.message[0]);
        	expect(vm.stopLoader).toHaveBeenCalled();
        });

        it('other backend error in try clause', function () {
        	var resetconfirmFormValid = true;
        	try_response = {};
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
