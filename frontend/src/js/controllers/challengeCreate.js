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
                    var formData = new FormData();
                    formData.append("zip_configuration", vm.input_file);

                    parameters.data = formData;

                    parameters.token = userKey;
                    parameters.callback = {
                        onSuccess: function(response) {
                            utilities.hideLoader();
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
                            utilities.hideLoader();
                            var error = response.data;
                            angular.element(".file-path").val(null);
                            $rootScope.notify("error", error.error);
                            vm.stopLoader();
                        }
                    };
                }
                utilities.showLoader();
                utilities.sendRequest(parameters, 'header', 'upload');
            }
            else {
                angular.element(".file-path").val(null);
                $rootScope.notify("info", "Please select a challenge host team!");
            }
        };
    }
})();

