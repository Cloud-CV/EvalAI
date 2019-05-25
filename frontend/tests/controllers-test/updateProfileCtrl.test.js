'use strict';

describe('Unit tests for update profile controller', function () {
    beforeEach(angular.mock.module('evalai'));

    var $controller, $rootScope, $scope, utilities, $state, vm;

    beforeEach(inject(function (_$controller_, _$rootScope_, _utilities_, _$state_,) {
        $controller = _$controller_;
        $rootScope = _$rootScope_;
        utilities = _utilities_;
        $state =_$state_;

        $scope = $rootScope.$new();
        vm = $controller('updateProfileCtrl', {$scope: $scope});
    }));

    describe('Global variables', function () {
        it('has default values', function () {
            expect(vm.wrnMsg).toEqual({});
            expect(vm.isValid).toEqual({});
            expect(vm.user).toEqual({});
            expect(vm.isFormError).toBeFalsy();
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
    });

    describe('Unit tests for `updateProfile` function', function () {
        var success, tryClauseResponse;
        var updateProfileLoaderMessage = "Updating Your Profile";
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
            spyOn(vm, 'startLoader');
            spyOn(vm, 'stopLoader');
            vm.user.username = "abc123";
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
            expect(vm.startLoader).toHaveBeenCalledWith(updateProfileLoaderMessage);
            expect($rootScope.notify).toHaveBeenCalledWith("success", "Profile updated successfully!");
            expect($state.go).toHaveBeenCalledWith('web.profile');
            expect(vm.stopLoader).toHaveBeenCalled();
        });

        it('when username is invalid', function () {
            var resetconfirmFormValid = true;
            tryClauseResponse = usernameInvalid;
            success = false;

            vm.updateProfile(resetconfirmFormValid);
            expect(vm.startLoader).toHaveBeenCalledWith(updateProfileLoaderMessage);
            expect(vm.stopLoader).toHaveBeenCalled();
            expect(vm.isFormError).toBeTruthy();
            expect(vm.FormError).toEqual(tryClauseResponse.username[0]);
            expect(vm.stopLoader).toHaveBeenCalled();
        });

        it('when firstname is invalid', function () {
            var resetconfirmFormValid = true;
            tryClauseResponse = firstnameInvalid;
            success = false;

            vm.updateProfile(resetconfirmFormValid);
            expect(vm.startLoader).toHaveBeenCalledWith(updateProfileLoaderMessage);
            expect(vm.stopLoader).toHaveBeenCalled();
            expect(vm.isFormError).toBeTruthy();
            expect(vm.FormError).toEqual(tryClauseResponse.first_name[0]);
            expect(vm.stopLoader).toHaveBeenCalled();
        });

        it('when lastname is invalid', function () {
            var resetconfirmFormValid = true;
            tryClauseResponse = lastnameInvalid;
            success = false;

            vm.updateProfile(resetconfirmFormValid);
            expect(vm.startLoader).toHaveBeenCalledWith(updateProfileLoaderMessage);
            expect(vm.stopLoader).toHaveBeenCalled();
            expect(vm.isFormError).toBeTruthy();
            expect(vm.FormError).toEqual(tryClauseResponse.last_name[0]);
            expect(vm.stopLoader).toHaveBeenCalled();
        });

        it('when affiliation is invalid', function () {
            var resetconfirmFormValid = true;
            tryClauseResponse = affiliationInvalid;
            success = false;

            vm.updateProfile(resetconfirmFormValid);
            expect(vm.startLoader).toHaveBeenCalledWith(updateProfileLoaderMessage);
            expect(vm.stopLoader).toHaveBeenCalled();
            expect(vm.isFormError).toBeTruthy();
            expect(vm.FormError).toEqual(tryClauseResponse.affiliation[0]);
            expect(vm.stopLoader).toHaveBeenCalled();
        });

        it('other backend error in try clause', function () {
            var resetconfirmFormValid = true;
            tryClauseResponse = {};
            success = false;

            vm.updateProfile(resetconfirmFormValid);
            expect(vm.isDisabled).toBeFalsy();
            expect(vm.isFormError).toBeTruthy();
            expect($rootScope.notify).toHaveBeenCalledWith("error", "Some error have occured . Please try again !");
            expect(vm.stopLoader).toHaveBeenCalled();
        });

        it('backend error with catch clause', function () {
            var resetconfirmFormValid = true;
            success = null;

            vm.updateProfile(resetconfirmFormValid);
            expect(vm.isDisabled).toBeFalsy();
            expect($rootScope.notify).toHaveBeenCalled();
            expect(vm.stopLoader).toHaveBeenCalled();
        });

        it('invalid form submission', function () {
            var resetconfirmFormValid = false;
            vm.updateProfile(resetconfirmFormValid);
            expect($rootScope.notify).toHaveBeenCalledWith("error", "Form fields are not valid!");
            expect(vm.stopLoader).toHaveBeenCalled();
        });
    });
});
