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

describe('Unit tests for getting user profile', function() {
    var utilities, $rootScope, vm;
    var successResponse = {
        status: 200,
        data: {
            name: 'Test User'
        }
    };
    var errorResponse = {
        status: 400,
        data: 'error'
    };

    beforeEach(angular.mock.module('evalai'));

    beforeEach(inject(function(_utilities_, _$rootScope_) {
        utilities = _utilities_;
        $rootScope = _$rootScope_;
        vm = {
            user: null
        };

        spyOn(utilities, 'sendRequest').and.callFake(function(parameters) {
            if (parameters.url === 'auth/user/') {
                parameters.callback.onSuccess(successResponse);
            } else {
                parameters.callback.onError(errorResponse);
            }
        });

        spyOn($rootScope, 'notify');
    }));

    it('gets user profile and sets vm.user', function() {
        var userKey = 'testUserKey';
        var parameters = {
            url: 'auth/user/',
            method: 'GET',
            token: userKey,
            callback: {
                onSuccess: function(response) {
                    var status = response.status;
                    var result = response.data;
                    if (status == 200) {
                        vm.user = result;
                    }
                },
                onError: function() {
                    $rootScope.notify("error", "Error in loading profile, please try again later !");
                }
            }
        };

        utilities.sendRequest(parameters);

        expect(vm.user).toEqual(successResponse.data);
        expect($rootScope.notify).not.toHaveBeenCalled();
    });

    it('handles error when getting user profile', function() {
        var userKey = 'testUserKey';
        var parameters = {
            url: 'auth/user_error/',
            method: 'GET',
            token: userKey,
            callback: {
                onSuccess: function(response) {
                    var status = response.status;
                    var result = response.data;
                    if (status == 200) {
                        vm.user = result;
                    }
                },
                onError: function() {
                    $rootScope.notify("error", "Error in loading profile, please try again later !");
                }
            }
        };

        utilities.sendRequest(parameters);

        expect(vm.user).toBeNull();
        expect($rootScope.notify).toHaveBeenCalledWith('error', 'Error in loading profile, please try again later !');
    });
});

describe('Unit tests for updateProfile function', function() {
    var vm;

    beforeEach(angular.mock.module('evalai'));

    beforeEach(inject(function() {
        vm = {
            user: {
                github_url: null,
                google_scholar_url: null,
                linkedin_url: null
            },
            isURLValid: function(url) {
                return url.length <= 200;
            },
            updateProfile: function(resetconfirmFormValid) {
                if (resetconfirmFormValid) {
                    this.user.github_url = this.user.github_url === null ? "" : this.user.github_url;
                    this.user.google_scholar_url = this.user.google_scholar_url === null ? "" : this.user.google_scholar_url;
                    this.user.linkedin_url = this.user.linkedin_url === null ? "" : this.user.linkedin_url;

                    if (!this.isURLValid(this.user.github_url)) {
                        this.isFormError = true;
                        this.FormError = "Github URL length should not be greater than 200!";
                        return;
                    } else if (!this.isURLValid(this.user.google_scholar_url)) {
                        this.isFormError = true;
                        this.FormError = "Google Scholar URL length should not be greater than 200!";
                        return;
                    } else if (!this.isURLValid(this.user.linkedin_url)) {
                        this.isFormError = true;
                        this.FormError = "LinkedIn URL length should not be greater than 200!";
                        return;
                    }
                }
            }
        };
    }));

    it('updates profile when form is valid', function() {
        vm.user.github_url = 'https://github.com/test';
        vm.user.google_scholar_url = 'https://scholar.google.com/test';
        vm.user.linkedin_url = 'https://linkedin.com/in/test';
        vm.updateProfile(true);
        expect(vm.isFormError).toBeUndefined();
        expect(vm.FormError).toBeUndefined();
    });

    it('does not update profile when form is invalid', function() {
        vm.user.github_url = 'https://github.com/test' + 'a'.repeat(200);
        vm.updateProfile(true);
        expect(vm.isFormError).toBe(true);
        expect(vm.FormError).toBe('Github URL length should not be greater than 200!');
    });
});

describe('Unit tests for isURLValid function', function() {
    var vm;

    beforeEach(angular.mock.module('evalai'));

    beforeEach(inject(function() {
        vm = {
            isURLValid: function(url) {
                if (url === undefined || url === null) {
                    return true;
                }
                return (url.length <= 200);
            }
        };
    }));

    it('returns true when URL is undefined', function() {
        expect(vm.isURLValid(undefined)).toBe(true);
    });

    it('returns true when URL is null', function() {
        expect(vm.isURLValid(null)).toBe(true);
    });

    it('returns true when URL length is less than or equal to 200', function() {
        var url = 'https://test.com/' + 'a'.repeat(182); 
        expect(vm.isURLValid(url)).toBe(true);
    });

    it('returns false when URL length is greater than 200', function() {
        var url = 'https://test.com/' + 'a'.repeat(201);
        expect(vm.isURLValid(url)).toBe(false);
    });
});