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
            return $controller('profileCtrl', { $scope: $scope });
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
            expect(vm.imgUrlObj).toEqual({ profilePic: "dist/images/spaceman.png" });
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
        var usernameInvalid = {
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
            spyOn($state, 'reload');
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
                } else if (success == null) {
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

        it('when university is invalid', function () {
            var resetconfirmFormValid = true;
            tryClauseResponse = universityInvalid;
            success = false;

            vm.updateProfile(resetconfirmFormValid);
            expect(vm.isFormError).toBeTruthy();
            expect(vm.FormError).toEqual(tryClauseResponse.university[0]);
        });

        it('when address_street is invalid', function () {
            var resetconfirmFormValid = true;
            tryClauseResponse = streetInvalid;
            success = false;

            vm.updateProfile(resetconfirmFormValid);
            expect(vm.isFormError).toBeTruthy();
            expect(vm.FormError).toEqual(tryClauseResponse.address_street[0]);
        });

        it('when address_city is invalid', function () {
            var resetconfirmFormValid = true;
            tryClauseResponse = cityInvalid;
            success = false;

            vm.updateProfile(resetconfirmFormValid);
            expect(vm.isFormError).toBeTruthy();
            expect(vm.FormError).toEqual(tryClauseResponse.address_city[0]);
        });

        it('when address_state is invalid', function () {
            var resetconfirmFormValid = true;
            tryClauseResponse = stateInvalid;
            success = false;

            vm.updateProfile(resetconfirmFormValid);
            expect(vm.isFormError).toBeTruthy();
            expect(vm.FormError).toEqual(tryClauseResponse.address_state[0]);
        });

        it('when address_country is invalid', function () {
            var resetconfirmFormValid = true;
            tryClauseResponse = countryInvalid;
            success = false;

            vm.updateProfile(resetconfirmFormValid);
            expect(vm.isFormError).toBeTruthy();
            expect(vm.FormError).toEqual(tryClauseResponse.address_country[0]);
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

        it('should set isFormError and notify if URL is invalid', function () {
            var resetconfirmFormValid = true;
            spyOn(vm, 'isURLValid').and.returnValue(false);
            vm.user.github_url = "a".repeat(201); // invalid URL
            vm.updateProfile(resetconfirmFormValid, 'github_url');
            expect(vm.isFormError).toBe(true);
            expect($rootScope.notify).toHaveBeenCalledWith("error", "URL length should not be greater than 200 or is in invalid format!");
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

        it('should allow saving a single field when other fields are blank', function () {
            var resetconfirmFormValid = true;
            vm.user.first_name = "John";
            vm.user.last_name = "";
            vm.user.address_city = "";
            vm.user.address_state = "";
            vm.user.address_street = "";
            vm.user.address_country = "";
            vm.user.university = "";
            vm.user.is_profile_fields_locked = false;

            spyOn(utilities, 'sendRequest').and.callFake(function (parameters) {
                // Verify only the edited field + non-empty fields are sent
                expect(parameters.data.first_name).toEqual("John");
                expect(parameters.data.last_name).toBeUndefined();
                expect(parameters.data.address_city).toBeUndefined();
                parameters.callback.onSuccess({ data: 'success', status: 200 });
            });

            vm.updateProfile(resetconfirmFormValid, 'first_name');
            expect(utilities.sendRequest).toHaveBeenCalled();
            expect($rootScope.notify).toHaveBeenCalledWith("success", "Profile updated successfully!");
        });

        it('should include non-empty fields even when not the field being edited', function () {
            var resetconfirmFormValid = true;
            vm.user.first_name = "John";
            vm.user.last_name = "Doe";
            vm.user.address_city = "Boston";
            vm.user.address_state = "";
            vm.user.address_street = "";
            vm.user.address_country = "";
            vm.user.university = "";
            vm.user.is_profile_fields_locked = false;

            spyOn(utilities, 'sendRequest').and.callFake(function (parameters) {
                // first_name is being edited, last_name and address_city are non-empty
                expect(parameters.data.first_name).toEqual("John");
                expect(parameters.data.last_name).toEqual("Doe");
                expect(parameters.data.address_city).toEqual("Boston");
                expect(parameters.data.address_state).toBeUndefined();
                parameters.callback.onSuccess({ data: 'success', status: 200 });
            });

            vm.updateProfile(resetconfirmFormValid, 'first_name');
            expect(utilities.sendRequest).toHaveBeenCalled();
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

    describe('Unit tests for downloadToken function', function () {
        it('should create an anchor and trigger download', function () {
            vm.jsonResponse = { token: 'abc123' };
            // Mock angular.element to return a fake anchor
            var dispatchEventSpy = jasmine.createSpy('dispatchEvent');
            var anchorMock = [{
                dispatchEvent: dispatchEventSpy
            }];
            anchorMock.attr = jasmine.createSpy('attr');
            spyOn(window.angular, 'element').and.returnValue(anchorMock);

            // Mock document.createEvent and its initMouseEvent
            var evMock = {};
            evMock.initMouseEvent = jasmine.createSpy('initMouseEvent');
            spyOn(document, 'createEvent').and.returnValue(evMock);

            vm.downloadToken();

            expect(window.angular.element).toHaveBeenCalledWith('<a/>');
            expect(anchorMock.attr).toHaveBeenCalledWith({
                href: jasmine.stringMatching(/^data:text\/json/),
                download: 'token.json'
            });
            expect(document.createEvent).toHaveBeenCalledWith('MouseEvents');
            expect(evMock.initMouseEvent).toHaveBeenCalledWith(
                "click", true, false, self, 0, 0, 0, 0, 0, false, false, false, false, 0, null
            );
            expect(dispatchEventSpy).toHaveBeenCalledWith(evMock);
        });
    });

    describe('Unit tests for refreshToken function', function () {
        beforeEach(function () {
            spyOn(utilities, 'storeData');
            spyOn($rootScope, 'notify');
            spyOn(utilities, 'sendRequest').and.callFake(function (params) {
                // Save params for manual invocation
                utilities._refreshParams = params;
            });
        });

        it('should refresh token and handle success', function () {
            vm.jsonResponse = {};
            vm.token = '';
            vm.refreshToken();
            // Simulate backend success
            var response = { data: { token: 'newtoken' } };
            utilities._refreshParams.callback.onSuccess(response);

            expect(vm.jsonResponse).toEqual(response.data);
            expect(vm.token).toEqual('newtoken');
            expect(utilities.storeData).toHaveBeenCalledWith('refreshJWT', 'newtoken');
            expect($rootScope.notify).toHaveBeenCalledWith("success", "Token generated successfully.");
        });

        it('should handle error on refresh token', function () {
            vm.refreshToken();
            var response = { data: { detail: 'fail' } };
            utilities._refreshParams.callback.onError(response);

            expect($rootScope.notify).toHaveBeenCalledWith("error", 'fail');
        });
    });

    describe('Unit tests for editprofileDialog function', function () {
        beforeEach(function () {
            spyOn($mdDialog, 'show');
        });

        const cases = [
            { id: 'first_name', title: 'First Name', editid: 'first_name' },
            { id: 'last_name', title: 'Last Name', editid: 'last_name' },
            { id: 'affiliation', title: 'Affiliation', editid: 'affiliation' },
            { id: 'university', title: 'University', editid: 'university' },
            { id: 'address_street', title: 'Street Address', editid: 'address_street' },
            { id: 'address_city', title: 'City', editid: 'address_city' },
            { id: 'address_state', title: 'State', editid: 'address_state' },
            { id: 'address_country', title: 'Country', editid: 'address_country' },
            { id: 'github_url', title: 'Github URL', editid: 'github_url' },
            { id: 'google_scholar_url', title: 'Google Scholar URL', editid: 'google_scholar_url' },
            { id: 'linkedin_url', title: 'Linkedin URL', editid: 'linkedin_url' },
        ];

        cases.forEach(function (testCase) {
            it('should set titleInput and editid for ' + testCase.id, function () {
                var ev = { currentTarget: { id: testCase.id } };
                vm.editprofileDialog(ev);
                expect(vm.titleInput).toEqual(testCase.title);
                expect(vm.editid).toEqual(testCase.editid);
                expect($mdDialog.show).toHaveBeenCalledWith(jasmine.objectContaining({
                    scope: $scope,
                    preserveScope: true,
                    targetEvent: ev,
                    templateUrl: 'dist/views/web/profile/edit-profile/edit-profile.html',
                    escapeToClose: false
                }));
            });
        });
    });

    describe('Unit tests for changePassword function', function () {
        beforeEach(function () {
            spyOn($rootScope, 'notify');
            spyOn($state, 'go');
            vm.user = {
                old_password: 'old',
                new_password1: 'new1',
                new_password2: 'new2'
            };
            $state.params = { user_id: 1 };
        });

        it('should call notify and go to AuthToken on success', function () {
            spyOn(utilities, 'sendRequest').and.callFake(function (params) {
                params.callback.onSuccess();
            });
            vm.changePassword(true);
            expect(vm.user.error).toBe(false);
            expect($rootScope.notify).toHaveBeenCalledWith("success", "Your password has been changed successfully!");
            expect($state.go).toHaveBeenCalledWith('web.profile.AuthToken');
        });

        it('should handle old_password error', function () {
            spyOn(utilities, 'sendRequest').and.callFake(function (params) {
                params.callback.onError({
                    data: { old_password: ["Old password error"] }
                });
            });
            vm.changePassword(true);
            expect(vm.user.error).toBe("Failed");
            expect(vm.isFormError).toBe(true);
            expect(vm.FormError).toBe("Old password error");
            expect($rootScope.notify).toHaveBeenCalledWith("error", "Old password error");
        });

        it('should handle new_password1 error', function () {
            spyOn(utilities, 'sendRequest').and.callFake(function (params) {
                params.callback.onError({
                    data: { new_password1: ["New password1 error"] }
                });
            });
            vm.changePassword(true);
            expect(vm.FormError).toBe("New password1 error");
            expect($rootScope.notify).toHaveBeenCalledWith("error", "New password1 error");
        });

        it('should handle new_password2 error', function () {
            spyOn(utilities, 'sendRequest').and.callFake(function (params) {
                params.callback.onError({
                    data: { new_password2: ["New password2 error"] }
                });
            });
            vm.changePassword(true);
            expect(vm.FormError).toBe("New password2 error");
            expect($rootScope.notify).toHaveBeenCalledWith("error", "New password2 error");
        });

        it('should handle error in catch clause', function () {
            spyOn(utilities, 'sendRequest').and.callFake(function (params) {
                params.callback.onError({
                    data: null
                });
            });
            // Force error in try-catch
            spyOn(Object, 'values').and.throwError('Test error');
            vm.changePassword(true);
            expect(vm.FormError).toBe("Something went wrong! Please refresh the page and try again.");
            expect($rootScope.notify).toHaveBeenCalledWith("error", "Something went wrong! Please refresh the page and try again.");
        });

        it('should notify if form is invalid', function () {
            vm.changePassword(false);
            expect($rootScope.notify).toHaveBeenCalledWith("error", "Something went wrong! Please refresh the page and try again.");
        });
    });

    describe('Unit tests for toggleOldPasswordVisibility function', function () {
        it('should toggle $rootScope.canShowOldPassword from false to true', function () {
            $rootScope.canShowOldPassword = false;
            vm.toggleOldPasswordVisibility();
            expect($rootScope.canShowOldPassword).toBe(true);
        });

        it('should toggle $rootScope.canShowOldPassword from true to false', function () {
            $rootScope.canShowOldPassword = true;
            vm.toggleOldPasswordVisibility();
            expect($rootScope.canShowOldPassword).toBe(false);
        });
    });

    describe('Unit tests for toggleNewPasswordVisibility function', function () {
        it('should toggle $rootScope.canShowNewPassword from false to true', function () {
            $rootScope.canShowNewPassword = false;
            vm.toggleNewPasswordVisibility();
            expect($rootScope.canShowNewPassword).toBe(true);
        });

        it('should toggle $rootScope.canShowNewPassword from true to false', function () {
            $rootScope.canShowNewPassword = true;
            vm.toggleNewPasswordVisibility();
            expect($rootScope.canShowNewPassword).toBe(false);
        });
    });

    describe('Unit tests for toggleNewConfirmVisibility function', function () {
        it('should toggle $rootScope.canShowNewConfirmPassword from false to true', function () {
            $rootScope.canShowNewConfirmPassword = false;
            vm.toggleNewConfirmVisibility();
            expect($rootScope.canShowNewConfirmPassword).toBe(true);
        });

        it('should toggle $rootScope.canShowNewConfirmPassword from true to false', function () {
            $rootScope.canShowNewConfirmPassword = true;
            vm.toggleNewConfirmVisibility();
            expect($rootScope.canShowNewConfirmPassword).toBe(false);
        });
    });
});
