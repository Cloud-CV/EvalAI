// Invoking IIFE for create challenge using ui
(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('CreateChallengeUsingUiCtrl', CreateChallengeUsingUiCtrl);

    CreateChallengeUsingUiCtrl.$inject = ['utilities', 'loaderService', '$rootScope', '$state'];

    function CreateChallengeUsingUiCtrl(utilities, loaderService, $rootScope, $state) {
        var vm = this;
        var userKey = utilities.getData('userKey');
        vm.hostTeamId = utilities.getData('challengeHostTeamId');
        vm.wrnMsg = {};
        vm.isValid = {};
        vm.isFormError = false;
        vm.challengeEvalScript = null;
        vm.challengeTitle = null;
        vm.formError = {};

        // varibales to manage the forms
        vm.step1 = true; 
        vm.step2 = false;
        vm.step3 = false;
        vm.step4 = false;
        vm.step5 = false;
        vm.challengeEnableForum = false;
        vm.challengePublicallyAvailable = false;

        // start loader
        vm.startLoader = loaderService.startLoader;

        // stop loader
        vm.stopLoader = loaderService.stopLoader;

        // function to create a Challenge
        vm.challengeCreate = function(challengeCreateFormValid) {
            if (vm.hostTeamId) {
                if (challengeCreateFormValid) {
                    if (vm.challengeEvalScript && vm.challengeTitle) {
                        var parameters = {};
                        parameters.method = 'POST';
                        parameters.url = 'challenges/challenge_host_team/'+ vm.hostTeamId + '/challenge';
                        var formdata = new FormData();
                        formdata.append("title", vm.challengeTitle);
                        formdata.append("short_description", vm.challengeShortDescription);
                        formdata.append("description", vm.challengeDescription);
                        formdata.append("terms_and_conditions", vm.challengeTermsAndConditions);
                        formdata.append("submission_guidelines", vm.challengeSubmissionGuidelines);
                        formdata.append("evaluation_details", vm.challengeEvaluationDetails);
                        formdata.append("published", vm.challengePublicallyAvailable);
                        formdata.append("enable_forum", vm.challengeEnableForum);
                        formdata.append("start_date", vm.challengeStartDate.format('YYYY-MM-DDThh:mm:ss[Z]'));
                        formdata.append("end_date", vm.challengeEndDate.format('YYYY-MM-DDThh:mm:ss[Z]'));
                        formdata.append("image", vm.challengeImage);
                        formdata.append("evaluation_script", vm.challengeEvalScript);
                        formdata.append("featured", false);

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
                                    $rootScope.notify("success", "Step 1 is completed");
                                    utilities.storeData('challenge', data);
                                    vm.challengeId = data.id;
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

        vm.leaderboardIndexArray = [];

        vm.getLeaderboardIndex = function(index){
            vm.leaderboardIndexArray.push(index);
        };

        vm.addNewLeaderboard = function() {
            vm.leaderboards.push({"leaderboardId": null, "schema": null});
        };

        vm.removeNewLeaderboard = function() {
            var arrLen = vm.leaderboardIndexArray.length;
            vm.leaderboards.splice(vm.leaderboardIndexArray[arrLen-1], 1);
            vm.leaderboardIndexArray.pop();
        };

        vm.leaderboardCreate = function(leaderboardCreateFormValid){
            if (leaderboardCreateFormValid){
                var parameters = {};
                parameters.method = 'POST';
                parameters.url = 'challenges/challenge/create/leaderboard/step_2/';
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
                            $rootScope.notify("success", "Step 2 is completed");
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


        // function to create a Challenge Phase
        vm.challengePhases = [
            {
             "name": null,
             "description": null,
             "codename": null,
             "max_submissions_per_day": null,
             "max_submissions": null,
             "start_date": null,
             "end_date": null,
             "test_annotation": null,
             "is_public": null,
             "leaderboard_public": null
            }
        ];

        vm.challengePhaseIndexArray = [];

        vm.getChallengePhaseIndex = function(index){
            vm.challengePhaseIndexArray.push(index);
        };

        vm.addNewChallengePhase = function() {
            vm.challengePhases.push({
             "name": null,
             "description": null,
             "codename": null,
             "max_submissions_per_day": null,
             "max_submissions": null,
             "start_date": null,
             "end_date": null,
             "test_annotation": null,
             "is_public": null,
             "leaderboard_public": null
            });
        };

        vm.removeChallengePhase = function() {
            var arrLen = vm.challengePhaseIndexArray.length;
            vm.challengePhases.splice(vm.challengePhaseIndexArray[arrLen-1], 1);
            vm.challengePhaseIndexArray.pop();
        };

        vm.challengePhaseCreate = function(challengePhaseCreateFormValid){
            if (challengePhaseCreateFormValid) {
                vm.challengeId = utilities.getData('challenge').id;

                for (var i=0; i<vm.challengePhases.length; i++) {
                    var challengePhaseList = [];
                    var formdata = new FormData();
                    var parameters = {};
                    formdata.append("name", vm.challengePhases[i].name);
                    formdata.append("description", vm.challengePhases[i].description);
                    formdata.append("codename", vm.challengePhases[i].codename);
                    formdata.append("max_submissions_per_day", vm.challengePhases[i].max_submissions_per_day);
                    formdata.append("max_submissions", vm.challengePhases[i].max_submissions);
                    formdata.append("start_date", vm.challengePhases[i].start_date.format('YYYY-MM-DDThh:mm:ss[Z]'));
                    formdata.append("end_date", vm.challengePhases[i].end_date.format('YYYY-MM-DDThh:mm:ss[Z]'));
                    formdata.append("leaderboard_public", vm.challengePhases[i].leaderboard_public || false);
                    formdata.append("is_public", vm.challengePhases[i].is_public || false);
                    formdata.append("test_annotation", vm.challengePhases[i].test_annotation);
                    formdata.append("challenge", vm.challengeId);

                    parameters.method = 'POST';
                    parameters.url = 'challenges/challenge/'+ vm.challengeId +'/challenge_phase';
                    parameters.data = formdata;
                    parameters.token = userKey;
                    parameters.callback = {
                        onSuccess: function(response) {
                            var status = response.status;
                            var data = response.data;
                            challengePhaseList.push(data);
                            if (status === 201) {
                                vm.step4 = true;
                                vm.step2 = false;
                                vm.step1 = false;
                                vm.step3 = false;
                                vm.isFormError = false;
                                utilities.storeData('challengePhase', challengePhaseList);
                                $rootScope.notify("success", "Step 3 is completed");
                            }
                        },
                        onError: function(response) {
                            var error = response.data;
                            vm.isFormError = true;
                            vm.formError = error;
                        }
                    };
                    utilities.sendRequest(parameters, 'header', 'upload');
                    }
            }
        };


        //function to create Dataset Splits
        vm.datasetSplits = [
            {
            "name": null,
            "codename": null
            }
        ];

        vm.datasetSplitIndexArray = [];

        vm.getdatasetSplitIndex = function(index) {
            vm.datasetSplitIndexArray.push(index);
        };

        vm.addNewDatasetSplit = function() {
            vm.datasetSplits.push({"name": null, "codename": null});
        };

        vm.removeNewDatasetSplit = function() {
            var arrLen = vm.datasetSplitIndexArray.length;
            vm.datasetSplits.splice(vm.datasetSplitIndexArray[arrLen-1], 1);
            vm.datasetSplitIndexArray.pop();
        };

        vm. datasetSplitCreate = function(datasetSplitCreateFormValid) {
            if (datasetSplitCreateFormValid) {
                var parameters = {};
                parameters.method = 'POST';
                parameters.url = 'challenges/challenge/create/dataset_split/step_4/';
                parameters.data = vm.datasetSplits;
                parameters.token = userKey;
                parameters.callback = {
                    onSuccess: function(response) {
                        var status = response.status;
                        var data = response.data;
                        if (status === 201) {
                            vm.step5 = true;
                            vm.step4 = false;
                            vm.step3 = false;
                            vm.step2 = false;
                            vm.step1 = false;
                            vm.isFormError = false;
                            $rootScope.notify("success", "Step 4 is completed!");
                            utilities.storeData('datasetSplit', data);
                            vm.challengePhase = utilities.getData('challengePhase');
                            vm.leaderboard = utilities.getData('leaderboard');
                            vm.datasetSplit = utilities.getData('datasetSplit');
                        }
                    },
                    onError: function(response){
                        var error = response.data;
                        var status = response.status;
                        if (status === 400) {
                            vm.isFormError = true;
                            vm.formError = error[0].codename;
                        }
                    }
                };
                utilities.sendRequest(parameters);
            } else {
                $rootScope.notify("error", "Some error have occured. Please try creating the challenge again!");
            }
        };


        //function to create Challenge Phase splits
        vm.challengePhaseSplits = [
            {"challenge_phase": null,
             "dataset_split": null,
             "leaderboard": null,
             "visibility": null}
        ];

        vm.challengePhaseSplitsIndexArray = [];

        vm.getChallengePhaseSplitsIndex = function(index){
            vm.challengePhaseSplitsIndexArray.push(index);
        };

        vm.addNewChallengePhaseSplit = function() {
            vm.challengePhaseSplits.push(
            {"challenge_phase": null,
             "dataset_split": null,
             "leaderboard": null,
             "visibility": null});
            };

        vm.removeNewChallengePhaseSplit = function() {
            var arrLen = vm.challengePhaseSplitsIndexArray.length;
            vm.challengePhaseSplits.splice(vm.challengePhaseSplitsIndexArray[arrLen-1], 1);
            vm.challengePhaseSplitsIndexArray.pop();
        };

        vm.visibility = [
            {'id': 1, 'name' : 'Host'},
            {'id': 2, 'name' : 'Owner And Host'},
            {'id': 3, 'name' : 'Public'}
        ];

        vm. challengePhaseSplitCreate = function(challengePhaseSplitCreateFormValid) {
            if (challengePhaseSplitCreateFormValid) {
                var parameters = {};
                parameters.method = 'POST';
                parameters.url = 'challenges/challenge/create/challenge_phase_split/step_5/';
                utilities.storeData('challengePhaseSplits', vm.challengePhaseSplits);

                parameters.data = vm.challengePhaseSplits;
                parameters.token = userKey;
                parameters.callback = {
                    onSuccess: function(response) {
                        var status = response.status;
                        if (status === 201) {
                            vm.step5 = false;
                            vm.step4 = false;
                            vm.step3 = false;
                            vm.step2 = false;
                            vm.step1 = false;
                            vm.isFormError = false;
                            $rootScope.notify('success', 'Challenge has been created successfully!');
                            utilities.deleteData('challenge');
                            utilities.deleteData('challengePhase');
                            utilities.deleteData('leaderboard');
                            utilities.deleteData('datasetSplit');
                            $state.go('web.dashboard');
                        }
                    },
                    onError: function(response){
                        var error = response.data;
                        var status = response.status;
                        if (status === 400) {
                            vm.isFormError = true;
                            vm.formdata = error;
                        }
                    }
                };
                utilities.sendRequest(parameters);
            } else {
                $rootScope.notify("error", "Some error have occured. Please try creating the challenge again!");
            }
        };
    }
})();
