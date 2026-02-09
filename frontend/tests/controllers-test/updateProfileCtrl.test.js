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

        it('should set vm.user on successful profile GET', function () {
            var testUser = { username: "testuser" };
            var parameters = {};
            spyOn(utilities, 'sendRequest').and.callFake(function (params) {
                params.callback.onSuccess({ status: 200, data: testUser });
            });
            
            var localVm = $controller('updateProfileCtrl', { $scope: $scope });
            expect(localVm.user).toEqual(testUser);
        });

        it('should notify error on failed profile GET', function () {
            spyOn(utilities, 'sendRequest').and.callFake(function (params) {
                params.callback.onError();
            });
            spyOn($rootScope, 'notify');
            
            $controller('updateProfileCtrl', { $scope: $scope });
            expect($rootScope.notify).toHaveBeenCalledWith("error", "Error in loading profile, please try again later !");
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
        var universityInvalid = {
            university: ["university error"]
        };
        var streetInvalid = {
            address_street: ["street error"]
        };
        var cityInvalid = {
            address_city: ["city error"]
        };
        var stateInvalid = {
            address_state: ["state error"]
        };
        var countryInvalid = {
            address_country: ["country error"]
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
            vm.user.university = "university";
            vm.user.address_street = "street";
            vm.user.address_city = "city";
            vm.user.address_state = "state";
            vm.user.address_country = "country";

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

        it('when university is invalid', function () {
            var resetconfirmFormValid = true;
            tryClauseResponse = universityInvalid;
            success = false;

            vm.updateProfile(resetconfirmFormValid);
            expect(vm.startLoader).toHaveBeenCalledWith(updateProfileLoaderMessage);
            expect(vm.stopLoader).toHaveBeenCalled();
            expect(vm.isFormError).toBeTruthy();
            expect(vm.FormError).toEqual(tryClauseResponse.university[0]);
            expect(vm.stopLoader).toHaveBeenCalled();
        });

        it('when address_street is invalid', function () {
            var resetconfirmFormValid = true;
            tryClauseResponse = streetInvalid;
            success = false;

            vm.updateProfile(resetconfirmFormValid);
            expect(vm.startLoader).toHaveBeenCalledWith(updateProfileLoaderMessage);
            expect(vm.stopLoader).toHaveBeenCalled();
            expect(vm.isFormError).toBeTruthy();
            expect(vm.FormError).toEqual(tryClauseResponse.address_street[0]);
            expect(vm.stopLoader).toHaveBeenCalled();
        });

        it('when address_city is invalid', function () {
            var resetconfirmFormValid = true;
            tryClauseResponse = cityInvalid;
            success = false;

            vm.updateProfile(resetconfirmFormValid);
            expect(vm.startLoader).toHaveBeenCalledWith(updateProfileLoaderMessage);
            expect(vm.stopLoader).toHaveBeenCalled();
            expect(vm.isFormError).toBeTruthy();
            expect(vm.FormError).toEqual(tryClauseResponse.address_city[0]);
            expect(vm.stopLoader).toHaveBeenCalled();
        });

        it('when address_state is invalid', function () {
            var resetconfirmFormValid = true;
            tryClauseResponse = stateInvalid;
            success = false;

            vm.updateProfile(resetconfirmFormValid);
            expect(vm.startLoader).toHaveBeenCalledWith(updateProfileLoaderMessage);
            expect(vm.stopLoader).toHaveBeenCalled();
            expect(vm.isFormError).toBeTruthy();
            expect(vm.FormError).toEqual(tryClauseResponse.address_state[0]);
            expect(vm.stopLoader).toHaveBeenCalled();
        });

        it('when address_country is invalid', function () {
            var resetconfirmFormValid = true;
            tryClauseResponse = countryInvalid;
            success = false;

            vm.updateProfile(resetconfirmFormValid);
            expect(vm.startLoader).toHaveBeenCalledWith(updateProfileLoaderMessage);
            expect(vm.stopLoader).toHaveBeenCalled();
            expect(vm.isFormError).toBeTruthy();
            expect(vm.FormError).toEqual(tryClauseResponse.address_country[0]);
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

        it('should set form error if github_url is too long', function () {
            var resetconfirmFormValid = true;
            vm.user.github_url = 'a'.repeat(201); 
            vm.user.google_scholar_url = '';
            vm.user.linkedin_url = '';
            vm.updateProfile(resetconfirmFormValid);
            expect(vm.isFormError).toBe(true);
            expect(vm.FormError).toBe("Github URL length should not be greater than 200!");
        });

        it('should set form error if google_scholar_url is too long', function () {
            var resetconfirmFormValid = true;
            vm.user.github_url = ''; 
            vm.user.google_scholar_url = 'b'.repeat(201); 
            vm.user.linkedin_url = '';
            vm.updateProfile(resetconfirmFormValid);
            expect(vm.isFormError).toBe(true);
            expect(vm.FormError).toBe("Google Scholar URL length should not be greater than 200!");
        });

        it('should set form error if linkedin_url is too long', function () {
            var resetconfirmFormValid = true;
            vm.user.github_url = ''; 
            vm.user.google_scholar_url = ''; 
            vm.user.linkedin_url = 'c'.repeat(201); 
            vm.updateProfile(resetconfirmFormValid);
            expect(vm.isFormError).toBe(true);
            expect(vm.FormError).toBe("LinkedIn URL length should not be greater than 200!");
        });

        it('should handle null address fields', function () {
            var resetconfirmFormValid = true;
            success = true;
            vm.user.address_street = null;
            vm.user.address_city = null;
            vm.user.address_state = null;
            vm.user.address_country = null;
            vm.user.university = null;
            vm.user.is_profile_fields_locked = true;

            vm.updateProfile(resetconfirmFormValid);
            expect(vm.user.address_street).toEqual("");
            expect(vm.user.address_city).toEqual("");
            expect(vm.user.address_state).toEqual("");
            expect(vm.user.address_country).toEqual("");
            expect(vm.user.university).toEqual("");
            expect($rootScope.notify).toHaveBeenCalledWith("success", "Profile updated successfully!");
        });

        it('should skip required field validation when is_profile_fields_locked is true', function () {
            var resetconfirmFormValid = true;
            success = true;
            vm.user.is_profile_fields_locked = true;
            vm.user.address_city = "";
            vm.user.address_state = "";

            vm.updateProfile(resetconfirmFormValid);
            expect(vm.startLoader).toHaveBeenCalledWith("Updating Your Profile");
            expect($rootScope.notify).toHaveBeenCalledWith("success", "Profile updated successfully!");
            expect(vm.stopLoader).toHaveBeenCalled();
        });

        it('should set FormError when required field is blank and not locked', function () {
            var resetconfirmFormValid = true;
            vm.user.is_profile_fields_locked = false;
            vm.user.address_city = "";

            vm.updateProfile(resetconfirmFormValid);
            expect(vm.isFormError).toBe(true);
            expect(vm.FormError).toBe("City cannot be blank.");
            expect(vm.startLoader).not.toHaveBeenCalled();
        });
    });
});
