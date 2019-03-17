// Invoking IIFE for create challenge page
(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('ChallengeCreateCtrl', ChallengeCreateCtrl);

    ChallengeCreateCtrl.$inject = ['utilities', 'loaderService', '$rootScope', '$state'];

    function ChallengeCreateCtrl(utilities, loaderService, $rootScope, $state) {
        var vm = this;
        var userKey = utilities.getData('userKey');
        var hostTeamId = utilities.getData('challengeHostTeamId');
        vm.wrnMsg = {};
        vm.isValid = {};
        vm.isFormError = false;
        vm.input_file = null;
        vm.formError = {};
        vm.progressPercentage = 0;
        vm.submissionInProgress = false;

        // start loader
        vm.startLoader = loaderService.startLoader;

        // stop loader
        vm.stopLoader = loaderService.stopLoader;

        // function to create a challenge using zip file.
    vm.challengeCreate = function() {
            if (hostTeamId) {
                var fileVal = angular.element(".file-path").val();

                if (fileVal === null || fileVal === "") {
                    vm.isFormError = true;
                    vm.formError = "Please upload file!";
                    vm.stopLoader();
                    
                }
                if (vm.input_file) {
                    var parameters = {};
                    parameters.url = 'challenges/challenge/challenge_host_team/' + hostTeamId + '/zip_upload/';
                    parameters.method = 'POST';
                    parameters.data = {
                        "zip_configuration": vm.input_file
                    };

                    parameters.token = userKey;
                    parameters.callback = {
                        onSuccess: function(response) {
                            vm.progressPercentage = 100;
                            vm.submissionInProgress = false;
                            var status = response.status;
                            var details =  response.data;
                            if (status === 201) {
                                var inputTypeFile = "input[type='file']";
                                angular.forEach(
                                    angular.element(inputTypeFile),
                                    function(inputElem) {
                                        angular.element(inputElem).val(null);
                                    }
                                );

                                angular.element(".file-path").val(null);
                                $rootScope.notify("success", details.success);
                                localStorage.removeItem('challengeHostTeamId');
                                $state.go('home');
                            }
                        },
                        onError: function(response) {
                            vm.submissionInProgress = false;
                            var error = response.data;
                            angular.element(".file-path").val(null);
                            $rootScope.notify("error", error.error);
                        },
                        onProgress: function (event) {
                            vm.progressPercentage = parseInt(100.0 * event.loaded / event.total);
                        }
                    };
                }
                vm.progressPercentage = 0;
                vm.submissionInProgress = true;
                utilities.sendRequest(parameters, 'header', 'upload');
            }
            else {
                angular.element(".file-path").val(null);
                $rootScope.notify("info", "Please select a challenge host team!");
            }
        };
    }
})();

