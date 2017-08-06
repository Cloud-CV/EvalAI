// Invoking IIFE for create challenge page
(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('ChallengeCreateCtrl', ChallengeCreateCtrl);

    ChallengeCreateCtrl.$inject = ['utilities', 'loaderService', '$rootScope', '$state', 'configService'];

    function ChallengeCreateCtrl(utilities, loaderService, $rootScope, $state, configService) {
        var vm = this;
        var EnvironmentConfig = configService;
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
                }
                if (vm.input_file) {
                    var parameters = {};
                    parameters.url =  EnvironmentConfig.CHALLENGE.CREATE_CHALLENGE_ENDPOINT + hostTeamId + '/zip_upload/';
                    parameters.method = 'POST';
                    var formData = new FormData();
                    formData.append("zip_configuration", vm.input_file);

                    parameters.data = formData;

                    parameters.token = userKey;
                    parameters.callback = {
                        onSuccess: function(response) {
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
                            var error = response.data;
                            angular.element(".file-path").val(null);
                            $rootScope.notify("error", error.error);
                            vm.stopLoader();
                        }
                    };
                }
                utilities.sendRequest(parameters, 'header', 'upload');
            }
            else {
                angular.element(".file-path").val(null);
                $rootScope.notify("info", "Please select a challenge host team!");
            }
        };
    }
})();

/* This code can be used for creating challenge using UI feature.     
                parameters.data = {
                "title": vm.title,
                "description": vm.description,
                "terms_and_conditions": vm.terms_and_conditions,
                "submission_guidelines": vm.submission_guidelines,
                "published": vm.published,
                "anonymous_leaderboard": vm.anonymous_leaderboard,
                "start_date": vm.start_date,
                "end_date": vm.end_date
            };

            parameters.callback = {
                onSuccess: function() {
                    // navigate to Challenge List Page
                    $state.go('web.challenge-main.challenge-list');
                },
                onError: function(response) {
                    var error = response.data;
                    angular.forEach(error, function(value, key) {
                        if (key == 'title') {
                            vm.isValid.title = true;
                            vm.wrnMsg.title = value[0];
                        }
                        if (key == 'description') {
                            vm.isValid.description = true;
                            vm.wrnMsg.description = value[0];
                        }
                        if (key == 'terms_and_conditions') {
                            vm.isValid.terms_and_conditions = true;
                            vm.wrnMsg.terms_and_conditions = value[0];
                        }
                        if (key == 'submission_guidelines') {
                            vm.isValid.submission_guidelines = true;
                            vm.wrnMsg.submission_guidelines = value[0];
                        }
                        if (key == 'published') {
                            vm.isValid.published = true;
                            vm.wrnMsg.published = value[0];
                        }
                        if (key == 'anonymous_leaderboard') {
                            vm.isValid.anonymous_leaderboard = true;
                            vm.wrnMsg.anonymous_leaderboard = value[0];
                        }
                        if (key == 'start_date') {
                            vm.isValid.start_date = true;
                            vm.wrnMsg.start_date = value[0];
                        }
                        if (key == 'end_date') {
                            vm.isValid.end_date = true;
                            vm.wrnMsg.end_date = value[0];
                        }
                    });
                }
            };*/
