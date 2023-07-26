// Invoking IIFE for profile view

(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('profileCtrl', profileCtrl);

    profileCtrl.$inject = ['utilities', '$rootScope', '$scope', '$mdDialog', 'moment', '$state'];

    function profileCtrl(utilities, $rootScope, $scope, $mdDialog, moment, $state) {
        var vm = this;

        vm.user = {};
        vm.countLeft = 0;
        vm.compPerc = 0;
        var count = 0;
        vm.inputType = 'password';
        vm.status = 'Show';
        vm.token = '';
        vm.expiresAt = '';

        // default parameters
        $rootScope.canShowOldPassword = false;
        $rootScope.canShowNewPassword = false;
        $rootScope.canShowNewConfirmPassword = false;

        utilities.hideLoader();

        vm.imgUrlObj = {
            profilePic: "dist/images/spaceman.png"
        };

        var hasImage = utilities.getData('avatar');
        if (!hasImage) {
            vm.imgUrl = _.sample(vm.imgUrlObj);
            utilities.storeData('avatar', vm.imgUrl);
        } else {
            vm.imgUrl = utilities.getData('avatar');
        }

        // get token
        var userKey = utilities.getData('userKey');

        var parameters = {};
        parameters.url = 'auth/user/';
        parameters.method = 'GET';
        parameters.token = userKey;
        parameters.callback = {
            onSuccess: function(response) {
                var status = response.status;
                var result = response.data;
                if (status == 200) {
                    for (var i in result) {
                        if (result[i] === "" || result[i] === undefined || result[i] === null) {
                            if (i === "linkedin_url" || i === "github_url" || i === "google_scholar_url") {
                                result[i] = "";
                            } else {
                                result[i] = "";
                            }
                            vm.countLeft = vm.countLeft + 1;
                        }
                        count = count + 1;
                    }
                    vm.compPerc = parseInt((vm.countLeft / count) * 100);

                    vm.user = result;
                    vm.userdetails = angular.copy(result);
                    vm.user.complete = 100 - vm.compPerc;

                }
            },
            onError: function(response) {
                var details = response.data;
                $rootScope.notify("error", details.error);
            }
        };

        utilities.sendRequest(parameters);

        parameters.url = 'accounts/user/get_auth_token';
        parameters.method = 'GET';
        parameters.token = userKey;
        parameters.callback = {
            onSuccess: function(response) {
                vm.jsonResponse = response.data;
                vm.token = response.data['token'];
                vm.expiresAt = moment.utc(response.data['expires_at']).local().format("MMM D, YYYY h:mm:ss A");
                let expiresAtOffset = new Date(vm.expiresAt).getTimezoneOffset();
                var timezone = moment.tz.guess();
                vm.expiresAtTimezone = moment.tz.zone(timezone).abbr(expiresAtOffset);
                var gmtOffset = moment().utcOffset();
                var gmtSign = gmtOffset >= 0 ? '+' : '-';
                var gmtHours = Math.abs(Math.floor(gmtOffset / 60));
                var gmtMinutes = Math.abs(gmtOffset % 60);
                 vm.gmtZone = 'GMT ' + gmtSign + ' ' + gmtHours + ':' + (gmtMinutes < 10 ? '0' : '') + gmtMinutes;
            },
            onError: function(response) {
                var details = response.data;
                $rootScope.notify("error", details['detail']);
            }
        };

        utilities.sendRequest(parameters);

        // Hide & show token function
        vm.hideShowPassword = function(){
            if (vm.inputType == 'password'){
                vm.inputType = 'text';
                vm.status = 'Hide';
            }
            else{
                vm.inputType = 'password';
                vm.status = 'Show';
            }
        };

        // Hide & show token function
        vm.showConfirmation = function(){
            $rootScope.notify("success", "Token copied to your clipboard.");
        };

        // Get token
        vm.getAuthTokenDialog = function(ev) {
            vm.titleInput = "";
            $mdDialog.show({
                scope: $scope,
                preserveScope: true,
                targetEvent: ev,
                templateUrl: 'dist/views/web/auth/get-token.html',
                escapeToClose: false
            });
        };

        vm.getAuthToken = function(getTokenForm) {
            if(!getTokenForm){
                vm.inputType = 'password';
                vm.status = 'Show';
                $mdDialog.hide();
            }
        };

        vm.downloadToken = function() {
            var anchor = angular.element('<a/>');
            anchor.attr({
                href: 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(vm.jsonResponse)),
                download: 'token.json'
            });

            // Create Event
            var ev = document.createEvent("MouseEvents");
                ev.initMouseEvent("click", true, false, self, 0, 0, 0, 0, 0, false, false, false, false, 0, null);
                // Fire event
                anchor[0].dispatchEvent(ev);

        };

        vm.refreshToken = function() {
            parameters.url = 'accounts/user/refresh_auth_token';
            parameters.method = 'GET';
            parameters.token = userKey;
            parameters.callback = {
                onSuccess: function(response) {
                    vm.jsonResponse = response.data;
                    vm.token = response.data['token'];
                    utilities.storeData('refreshJWT', vm.token);
                    $rootScope.notify("success", "Token generated successfully.");
                },
                onError: function(response) {
                    var details = response.data;
                    $rootScope.notify("error", details['detail']);
                }
            };
            utilities.sendRequest(parameters);
        };

        vm.isURLValid = function(url) {
            if (url === undefined || url === null) {
                return true;
            }
            return (url.length <= 200);
        };

        vm.editprofileDialog = function(ev) {
            switch (ev.currentTarget.id) {
                case "first_name":
                  vm.titleInput = "First Name";
                  vm.editid = "first_name";
                  break;
                case "last_name":
                  vm.titleInput = "Last Name";
                  vm.editid = "last_name";
                  break;
                case "affiliation":
                  vm.titleInput = "Affiliation";
                  vm.editid = "affiliation";
                  break;
                case "github_url":
                  vm.titleInput = "Github URL";
                  vm.editid = "github_url";
                  break;
                case "google_scholar_url":
                  vm.titleInput = "Google Scholar URL";
                  vm.editid = "google_scholar_url";
                  break;
                case "linkedin_url":
                  vm.titleInput = "Linkedin URL";
                  vm.editid = "linkedin_url";
                  break;
              }

            $mdDialog.show({
                scope: $scope,
                preserveScope: true,
                targetEvent: ev,
                templateUrl: 'dist/views/web/profile/edit-profile/edit-profile.html',
                escapeToClose: false
            });
        };

        // function to update Profile
        vm.updateProfile = function(resetconfirmFormValid, editid) {
            if (resetconfirmFormValid) {
                vm.user.github_url = vm.user.github_url === null ? "" : vm.user.github_url;
                vm.user.google_scholar_url = vm.user.google_scholar_url === null ? "" : vm.user.google_scholar_url;
                vm.user.linkedin_url = vm.user.linkedin_url === null ? "" : vm.user.linkedin_url;

                if (!vm.isURLValid(vm.user[editid])) {
                    vm.isFormError = true;
                    $rootScope.notify("error", "URL length should not be greater than 200 or is in invalid format!");
                    return;
                }

                var parameters = {};
                parameters.url = 'auth/user/';
                parameters.method = 'PUT';
                parameters.data = {
                    "first_name": vm.user.first_name,
                    "last_name": vm.user.last_name,
                    "affiliation": vm.user.affiliation,
                    "github_url": vm.user.github_url,
                    "google_scholar_url": vm.user.google_scholar_url,
                    "linkedin_url": vm.user.linkedin_url
                };
                parameters.token = userKey;
                parameters.callback = {
                    onSuccess: function(response) {
                        if (response.status == 200) {
                            $rootScope.notify("success", "Profile updated successfully!");
                            $mdDialog.hide();
                            // navigate to profile page
                            $state.reload();
                        }
                    },
                    onError: function(response) {
                        if (response.status == 400) {
                            vm.errorResponse = response;

                            vm.isFormError = true;
                            var isFirstname_valid, isLastname_valid, isAffiliation_valid;
                            try {
                                isFirstname_valid = typeof(response.data.first_name) !== 'undefined' ? true : false;
                                isLastname_valid = typeof(response.data.last_name) !== 'undefined' ? true : false;
                                isAffiliation_valid = typeof(response.data.affiliation) !== 'undefined' ? true : false;
                                if (isFirstname_valid) {
                                    vm.FormError = response.data.first_name[0];
                                } else if (isLastname_valid) {
                                    vm.FormError = response.data.last_name[0];
                                } else if (isAffiliation_valid) {
                                    vm.FormError = response.data.affiliation[0]; 
                                } else {
                                    $rootScope.notify("error", "Some error have occured . Please try again !");
                                }
                                $rootScope.notify("error", vm.FormError);

                            } catch (error) {
                                $rootScope.notify("error", error);
                            }
                        }

                    }
                };

                utilities.sendRequest(parameters);

            } else {
                $mdDialog.hide();
                $state.reload();

            }
        };

        // toggle old password visibility
        vm.toggleOldPasswordVisibility = function() {
            $rootScope.canShowOldPassword = !$rootScope.canShowOldPassword;
        };

        // toggle new password visibility
        vm.toggleNewPasswordVisibility = function() {
            $rootScope.canShowNewPassword = !$rootScope.canShowNewPassword;
        };

        // toggle new password again visibility
        vm.toggleNewConfirmVisibility = function() {
            $rootScope.canShowNewConfirmPassword = !$rootScope.canShowNewConfirmPassword;
        };

        // function to change password
        vm.changePassword = function(resetconfirmFormValid) {
            if(resetconfirmFormValid){
            var parameters = {};
            parameters.url = 'auth/password/change/';
            parameters.method = 'POST';
            parameters.data = {
                "old_password": vm.user.old_password,
                "new_password1": vm.user.new_password1,
                "new_password2": vm.user.new_password2,
                "uid": $state.params.user_id,
            };
            parameters.token = userKey;
                parameters.callback = {
                    onSuccess: function() {
                        vm.user.error = false;
                        $rootScope.notify("success", "Your password has been changed successfully!");
                        $state.go('web.profile.AuthToken');
                    },
                    onError: function(response) {
                        vm.user.error = "Failed";
                        vm.isFormError = true;
                        var oldpassword_valid ,password1_valid, password2_valid;
                        try {
                            oldpassword_valid = typeof(response.data.old_password) !== 'undefined' ? true : false;
                            password1_valid = typeof(response.data.new_password1) !== 'undefined' ? true : false;
                            password2_valid = typeof(response.data.new_password2) !== 'undefined' ? true : false;
                            if (oldpassword_valid) {
                                vm.FormError = Object.values(response.data.old_password).join(" ");
                            }else if (password1_valid) {
                                vm.FormError = Object.values(response.data.new_password1).join(" ");
                            } else if (password2_valid) {
                                vm.FormError = Object.values(response.data.new_password2).join(" ");
                            }
                        } catch (error) { 
                            vm.FormError = "Something went wrong! Please refresh the page and try again.";
                        }
                        $rootScope.notify("error", vm.FormError);
                    }
                };

                utilities.sendRequest(parameters);

            }else {
                $rootScope.notify("error", "Something went wrong! Please refresh the page and try again.");
            }
        };
    }

})();
