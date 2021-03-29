// Invoking IIFE for profile view

(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('profileCtrl', profileCtrl);

    profileCtrl.$inject = ['utilities', '$rootScope', '$scope', '$mdDialog'];

    function profileCtrl(utilities, $rootScope, $scope, $mdDialog) {
        var vm = this;

        vm.user = {};
        vm.countLeft = 0;
        vm.compPerc = 0;
        var count = 0;
        vm.inputType = 'password';
        vm.status = 'Show';
        vm.token = '';

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
                                result[i] = "-";
                            }
                            vm.countLeft = vm.countLeft + 1;
                        }
                        count = count + 1;
                    }
                    vm.compPerc = parseInt((vm.countLeft / count) * 100);

                    vm.user = result;
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
    }

})();
