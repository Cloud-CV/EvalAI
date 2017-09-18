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
        vm.step1 = false;
        vm.step2 = false;
        vm.step3 = false;
        vm.step4 = true;
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

// function to create a Challenge Phase
        vm.challenge_phases = [
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

        vm.addNewChallengePhase = function() {
            vm.challenge_phases.push({
             "name": null,
             "description": null,
             "codename": null,
             "max_submissions_per_day": 0,
             "max_submissions": 0,
             "start_date": null,
             "end_date": null,
             "test_annotation": null,
             "is_public": null,
             "leaderboard_public": null
            });
        };

        vm.removeNewChallengePhase = function(index) {
            vm.challenge_phases.splice(index, 1);
        };

        vm.challengePhaseCreate = function(challengePhaseCreateFormValid){
            if (challengePhaseCreateFormValid) {
                vm.challengeId = utilities.getData('challenge').id;

                for (var i=0; i<vm.challenge_phases.length; i++) {
                    var challengePhaseList = [];
                    var formdata = new FormData();
                    var parameters = {};
                    vm.challenge_phases[i].start_date = vm.formatDate(vm.challenge_phases[i].start_date);
                    vm.challenge_phases[i].end_date = vm.formatDate(vm.challenge_phases[i].end_date);
                    formdata.append("name", vm.challenge_phases[i].name);
                    formdata.append("description", vm.challenge_phases[i].description);
                    formdata.append("codename", vm.challenge_phases[i].codename);
                    formdata.append("max_submissions_per_day", vm.challenge_phases[i].max_submissions_per_day);
                    formdata.append("max_submissions", vm.challenge_phases[i].max_submissions);
                    formdata.append("start_date", vm.challenge_phases[i].start_date);
                    formdata.append("end_date", vm.challenge_phases[i].end_date);
                    formdata.append("leaderboard_public", vm.challenge_phases[i].leaderboard_public || false);
                    formdata.append("is_public", vm.challenge_phases[i].is_public || false);
                    formdata.append("test_annotation", vm.challenge_phases[i].test_annotation);
                    formdata.append("challenge", vm.challengeId);

                    // utilities.storeData("test_annotation"+i, vm.challenge_phases[i].test_annotation);

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
                                $rootScope.notify("success", "Step3 is completed");
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

        vm.addNewDatasetSplit = function() {
            vm.datasetSplits.push({"name": null, "codename": null});
        };

        vm.removeNewDatasetSplit = function(index) {
            vm.datasetSplits.splice(index, 1);
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
                console.log("datasetSplit");
            }
        };

//function to create Challenge Phase splits

        vm.challengePhaseSplits = [
            {"challenge_phase": null,
             "dataset_split": null,
             "leaderboard": null,
             "visibility": null}
        ];

        vm.addNewChallengePhaseSplit = function() {
            vm.challengePhaseSplits.push(
            {"challenge_phase": null,
             "dataset_split": null,
             "leaderboard": null,
             "visibility": null});
            };

        vm.removeNewChallengePhaseSplit = function(index) {
            vm.challengePhaseSplits.splice(index, 1);
        };

        vm.visibility = [
            {'id': 1, 'name' : 'Host'},
            {'id': 2, 'name' : 'Owner And Host'},
            {'id': 3, 'name' : 'Public'}
        ];

        vm.challenge = utilities.getData('challenge');
        vm.challengeImageName = utilities.getData('challengeImage');
        vm.evalScriptName = utilities.getData('evalScript');

        vm. challengePhaseSplitCreate = function(challengePhaseSplitCreateFormValid) {
            if (challengePhaseSplitCreateFormValid) {
                console.log("1");
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
                            vm.reviewScreen = true;
                            vm.step5 = false;
                            vm.step4 = false;
                            vm.step3 = false;
                            vm.step2 = false;
                            vm.step1 = false;
                            vm.isFormError = false;
                            $rootScope.notify("success", "Step 5 is completed!");
                            if (vm.reviewScreen == true){
                                        vm.challengePhaseSplitsData = utilities.getData('challengePhaseSplits');
                                        vm.challengePhase = utilities.getData('challengePhase');
                                        vm.leaderboard = utilities.getData('leaderboard');
                                        vm.datasetSplit = utilities.getData('datasetSplit');
                                        vm.data = [];
                                        for (var i=0; i<vm.challengePhaseSplitsData.length; i++) {
                                            vm.data.push({
                                            "challenge_phase": null,
                                            "dataset_split": null,
                                            "leaderboard": null,
                                            "visibility": null
                                            });

                                        for (var j=0; j<vm.challengePhase.length; j++) {
                                            if(vm.challengePhaseSplitsData[i].challenge_phase == vm.challengePhase[j].id) {
                                                vm.data[i].challenge_phase = vm.challengePhase[j].name;
                                            }

                                        }
                                        for (j=0; j<vm.datasetSplit.length; j++) {
                                            if(vm.challengePhaseSplitsData[i].dataset_split == vm.datasetSplit[j].id) {
                                                vm.data[i].dataset_split = vm.datasetSplit[j].name;
                                            }
                                        }
                                        for (j=0; j<vm.leaderboard.length; j++) {
                                            if (vm.challengePhaseSplitsData[i].leaderboard == vm.leaderboard[j].id) {
                                                vm.data[i].leaderboard = vm.leaderboard[j].schema;
                                            }
                                        }
                                        for (j=0; j<vm.visibility.length; j++) {
                                            if (vm.challengePhaseSplitsData[i].visibility == vm.visibility[j].id) {
                                                vm.data[i].visibility = vm.visibility[j].name;
                                            }
                                        }
                                    }
                            }
                            // utilities.deleteData('challenge');
                            // utilities.deleteData('challengePhase');
                            // utilities.deleteData('leaderboard');
                            // utilities.deleteData('datasetSplit');
                        }
                    },
                    onError: function(response){
                        var error = response.data;
                        var status = response.status;
                        if (status === 400) {
                            vm.isFormError = true;
                            vm.formdata = error;
                            console.log(error);
                        }
                    }
                };
                utilities.sendRequest(parameters);
            } else {
                console.log("ChallengePhaseSplit");
            }
        };

        vm.challengePhaseSplitsData = utilities.getData('challengePhaseSplits');
        vm.challengePhase = utilities.getData('challengePhase');
        vm.leaderboard = utilities.getData('leaderboard');
        vm.datasetSplit = utilities.getData('datasetSplit');
        vm.data = [];
        for (var i=0; i<vm.challengePhaseSplitsData.length; i++) {
            vm.data.push({
            "challenge_phase": null,
            "dataset_split": null,
            "leaderboard": null,
            "visibility": null
            });

        for (var j=0; j<vm.challengePhase.length; j++) {
            if(vm.challengePhaseSplitsData[i].challenge_phase == vm.challengePhase[j].id) {
                vm.data[i].challenge_phase = vm.challengePhase[j].name;
            }

        }
        for (j=0; j<vm.datasetSplit.length; j++) {
            if(vm.challengePhaseSplitsData[i].dataset_split == vm.datasetSplit[j].id) {
                vm.data[i].dataset_split = vm.datasetSplit[j].name;
            }
        }
        for (j=0; j<vm.leaderboard.length; j++) {
            if (vm.challengePhaseSplitsData[i].leaderboard == vm.leaderboard[j].id) {
                vm.data[i].leaderboard = vm.leaderboard[j].schema;
            }
        }
        for (j=0; j<vm.visibility.length; j++) {
            if (vm.challengePhaseSplitsData[i].visibility == vm.visibility[j].id) {
                vm.data[i].visibility = vm.visibility[j].name;
            }
        }
    }


    }
})();
