// Invoking IIFE for update profile

(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('updateProfileCtrl', updateProfileCtrl);

    updateProfileCtrl.$inject = ['utilities', '$state', '$rootScope'];

    function updateProfileCtrl(utilities, $state, $rootScope) {
        var vm = this;
        var userKey = utilities.getData('userKey');
        vm.wrnMsg = {};
        vm.isValid = {};
        vm.user = {};
        vm.isFormError = false;

        vm.updateprofileContainer = angular.element('.update-profile-card');

        vm.startLoader = function(msg) {
            $rootScope.isLoader = true;
            $rootScope.loaderTitle = msg;
            vm.updateprofileContainer.addClass('low-screen');
        };

        // stop loader
        vm.stopLoader = function() {
            $rootScope.isLoader = false;
            $rootScope.loaderTitle = '';
            vm.updateprofileContainer.removeClass('low-screen');
        };

        // To get the previous profile data
        var parameters = {};
        parameters.url = 'auth/user/';
        parameters.method = 'GET';
        parameters.token = userKey;
        parameters.callback = {
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
        };

        utilities.sendRequest(parameters);

        vm.isURLValid = function(url) {
            if (url === undefined || url === null) {
                return true;
            }
            return (url.length <= 200);
        };

        // function to update Profile
        vm.updateProfile = function(resetconfirmFormValid) {
            if (resetconfirmFormValid) {
                vm.user.github_url = vm.user.github_url === null ? "" : vm.user.github_url;
                vm.user.google_scholar_url = vm.user.google_scholar_url === null ? "" : vm.user.google_scholar_url;
                vm.user.linkedin_url = vm.user.linkedin_url === null ? "" : vm.user.linkedin_url;
                vm.user.address_street = vm.user.address_street === null ? "" : vm.user.address_street;
                vm.user.address_city = vm.user.address_city === null ? "" : vm.user.address_city;
                vm.user.address_state = vm.user.address_state === null ? "" : vm.user.address_state;
                vm.user.address_country = vm.user.address_country === null ? "" : vm.user.address_country;
                vm.user.university = vm.user.university === null ? "" : vm.user.university;

                if (!vm.isURLValid(vm.user.github_url)) {
                    vm.isFormError = true;
                    vm.FormError = "Github URL length should not be greater than 200!";
                    return;
                } else if (!vm.isURLValid(vm.user.google_scholar_url)) {
                    vm.isFormError = true;
                    vm.FormError = "Google Scholar URL length should not be greater than 200!";
                    return;
                } else if (!vm.isURLValid(vm.user.linkedin_url)) {
                    vm.isFormError = true;
                    vm.FormError = "LinkedIn URL length should not be greater than 200!";
                    return;
                }

                // Required profile fields cannot be blank (skip when locked)
                if (!vm.user.is_profile_fields_locked) {
                    var requiredFields = [
                        { key: 'first_name', label: 'First name' },
                        { key: 'last_name', label: 'Last name' },
                        { key: 'address_street', label: 'Street address' },
                        { key: 'address_city', label: 'City' },
                        { key: 'address_state', label: 'State' },
                        { key: 'address_country', label: 'Country' },
                        { key: 'university', label: 'University' }
                    ];
                    for (var i = 0; i < requiredFields.length; i++) {
                        var field = requiredFields[i];
                        var value = vm.user[field.key];
                        if (!value || (typeof value === 'string' && !value.trim())) {
                            vm.isFormError = true;
                            vm.FormError = field.label + ' cannot be blank.';
                            return;
                        }
                    }
                }

                vm.startLoader("Updating Your Profile");
                var parameters = {};
                parameters.url = 'auth/user/';
                parameters.method = 'PUT';
                parameters.data = {
                    "username": vm.user.username,
                    "affiliation": vm.user.affiliation,
                    "github_url": vm.user.github_url,
                    "google_scholar_url": vm.user.google_scholar_url,
                    "linkedin_url": vm.user.linkedin_url
                };
                // Only include locked fields when profile is not locked
                if (!vm.user.is_profile_fields_locked) {
                    parameters.data.first_name = vm.user.first_name;
                    parameters.data.last_name = vm.user.last_name;
                    parameters.data.address_street = vm.user.address_street;
                    parameters.data.address_city = vm.user.address_city;
                    parameters.data.address_state = vm.user.address_state;
                    parameters.data.address_country = vm.user.address_country;
                    parameters.data.university = vm.user.university;
                }
                parameters.token = userKey;
                parameters.callback = {
                    onSuccess: function(response) {
                        if (response.status == 200) {
                            $rootScope.notify("success", "Profile updated successfully!");
                            // navigate to profile page
                            $state.go('web.profile');
                            vm.stopLoader();
                        }
                    },
                    onError: function(response) {
                        if (response.status == 400) {
                            vm.errorResponse = response;
                            vm.stopLoader();
                            vm.isFormError = true;
                            var isUsername_valid, isFirstname_valid, isLastname_valid, isAffiliation_valid;
                            var isUniversity_valid, isStreet_valid, isCity_valid, isState_valid, isCountry_valid;
                            try {
                                isUsername_valid = typeof(response.data.username) !== 'undefined' ? true : false;
                                isFirstname_valid = typeof(response.data.first_name) !== 'undefined' ? true : false;
                                isLastname_valid = typeof(response.data.last_name) !== 'undefined' ? true : false;
                                isAffiliation_valid = typeof(response.data.affiliation) !== 'undefined' ? true : false;
                                isUniversity_valid = typeof(response.data.university) !== 'undefined' ? true : false;
                                isStreet_valid = typeof(response.data.address_street) !== 'undefined' ? true : false;
                                isCity_valid = typeof(response.data.address_city) !== 'undefined' ? true : false;
                                isState_valid = typeof(response.data.address_state) !== 'undefined' ? true : false;
                                isCountry_valid = typeof(response.data.address_country) !== 'undefined' ? true : false;
                                if (isUsername_valid) {
                                    vm.FormError = response.data.username[0];
                                } else if (isFirstname_valid) {
                                    vm.FormError = response.data.first_name[0];
                                } else if (isLastname_valid) {
                                    vm.FormError = response.data.last_name[0];
                                } else if (isAffiliation_valid) {
                                    vm.FormError = response.data.affiliation[0];
                                } else if (isUniversity_valid) {
                                    vm.FormError = response.data.university[0];
                                } else if (isStreet_valid) {
                                    vm.FormError = response.data.address_street[0];
                                } else if (isCity_valid) {
                                    vm.FormError = response.data.address_city[0];
                                } else if (isState_valid) {
                                    vm.FormError = response.data.address_state[0];
                                } else if (isCountry_valid) {
                                    vm.FormError = response.data.address_country[0];
                                } else {
                                    $rootScope.notify("error", "Some error have occured . Please try again !");
                                }

                            } catch (error) {
                                $rootScope.notify("error", error);
                            }
                        }

                        vm.stopLoader();
                    }
                };

                utilities.sendRequest(parameters);

            } else {
                $rootScope.notify("error", "Form fields are not valid!");
                vm.stopLoader();
            }
        };
    }

})();
