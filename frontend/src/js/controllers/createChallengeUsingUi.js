// Invoking IIFE for create challenge using ui
(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('CreateChallengeUsingUiCtrl', CreateChallengeUsingUiCtrl);

    CreateChallengeUsingUiCtrl.$inject = ['utilities', 'loaderService', '$rootScope'];

    function CreateChallengeUsingUiCtrl(utilities, loaderService, $rootScope) {
        var vm = this;
        var userKey = utilities.getData('userKey');
        vm.hostTeamId = utilities.getData('challengeHostTeamId');
        vm.wrnMsg = {};
        vm.isValid = {};
        vm.isFormError = false;
        vm.challengeEvalScript = null;
        vm.challengeTitle = null;
        vm.formError = {};
        vm.step1 = true;
        vm.step2 = false;
        vm.step3 = false;
        vm.step4 = false;
        vm.step5 = false;
        vm.step6 = false;
        vm.reviewScreen = false;
        vm.challengeEnableForum = false;
        vm.challengePublicallyAvailable = false;

        // start loader
        vm.startLoader = loaderService.startLoader;

        // stop loader
        vm.stopLoader = loaderService.stopLoader;

        vm.formatDate = function(dateTimeObject) {          
            var dateTime = dateTimeObject.toISOString();
            var splitDateTime = dateTime.split("T");
            var date = splitDateTime[0];
            var time = splitDateTime[1].split(".")[0];
            return date + " " + time;
        };

// function to create a Challenge.
        vm.challengeCreate = function(challengeCreateFormValid) {
            if (vm.hostTeamId) {
                if (challengeCreateFormValid) {
                    if (vm.challengeEvalScript && vm.challengeTitle) {
                        var parameters = {};
                        parameters.method = 'POST';
                        parameters.url = 'challenges/challenge_host_team/'+ vm.hostTeamId + '/challenge';
                        var formdata = new FormData();
                        vm.challengeStartDate = vm.formatDate(vm.challengeStartDate);
                        vm.challengeEndDate = vm.formatDate(vm.challengeEndDate);
                        formdata.append("title", vm.challengeTitle);
                        formdata.append("short_description", vm.challengeShortDescription);
                        formdata.append("description", vm.challengeDescription);
                        formdata.append("terms_and_conditions", vm.challengeTermsAndConditions);
                        formdata.append("submission_guidelines", vm.challengeSubmissionGuidelines);
                        formdata.append("evaluation_details", vm.challengeEvaluationDetails);
                        formdata.append("published", vm.challengePublicallyAvailable);
                        formdata.append("enable_forum", vm.challengeEnableForum);
                        formdata.append("start_date", vm.challengeStartDate);
                        formdata.append("end_date", vm.challengeEndDate);
                        formdata.append("image", vm.challengeImage);
                        formdata.append("evaluation_script", vm.challengeEvalScript);

                        utilities.storeData('challengeImage', vm.challengeImage.name);
                        utilities.storeData('evalScript', vm.challengeEvalScript.name);

                        parameters.data = formdata;
                        parameters.token = userKey;
                        parameters.callback = {
                            onSuccess: function(response) {
                                var status = response.status;
                                var data = response.data;
                                if (status === 201)
                                {   
                                    vm.step2 = true;
                                    vm.step1 = false;
                                    vm.isFormError = false;
                                    $rootScope.notify("success", "step1 is completed");
                                    utilities.storeData('challenge', data);
                                }
                            },
                            onError: function(response) {
                                var error = response.data;
                                $rootScope.notify("error", error);
                            }
                        };
                        utilities.sendRequest(parameters, 'header', 'upload');
                    } else {
                        vm.isFormError = true;
                        var evalScriptFileVal = angular.element(".eval-script").val();
                        if (evalScriptFileVal === null || evalScriptFileVal === "") {
                            vm.formError = "Please upload Evaluation script file!";
                        } else {
                        vm.formError = "Please fill above details!";
                        }
                    }
                } else {
                    vm.isFormError = true;
                    evalScriptFileVal = angular.element(".eval-script").val();
                    if (evalScriptFileVal === null || evalScriptFileVal === "") {
                        vm.formError = "Please upload Evaluation script file!";
                    }else {
                        vm.formError = "Please fill above details!";
                    }
                }
            } else {
                angular.element(".file-path").val(null);
                $rootScope.notify("info", "Please select a challenge host team!");
            }
        };

//function to create a LeaderBoard
        vm.leaderboards = [
            {
            "leaderboardId": null,
            "schema": null
            }
        ];

        vm.addNewLeaderboard = function() {
            vm.leaderboards.push({"leaderboardId": null, "schema": null});
        };

        vm.removeNewLeaderboard = function(index) {
            vm.leaderboards.splice(index, 1);
        };

        vm.leaderboardCreate = function(leaderboardCreateFormValid){
            if (leaderboardCreateFormValid){
                var parameters = {};
                parameters.method = 'POST';
                parameters.url = 'challenges/challenge/leaderboard/step_2/';
                parameters.data = vm.leaderboards;
                parameters.token = userKey;
                parameters.callback = {
                    onSuccess: function(response) {
                        var status = response.status;
                        var data = response.data;
                        if (status === 201) {
                            vm.step3 = true;
                            vm.step2 = false;
                            vm.step1 = false;
                            vm.isFormError = false;
                            $rootScope.notify("success", "Step2 is completed");
                            utilities.storeData('leaderboard', data);
                        }
                    },
                    onError: function(response) {
                        var error = response.data;
                        var status = response.status;
                        if (status === 400){
                            vm.isFormError = true;
                            vm.formError = error;
                        }
                    }
                };
                utilities.sendRequest(parameters);
            }
        };

    }
})();
