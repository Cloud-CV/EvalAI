// Invoking IIFE for create challenge using ui
(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('challengeCreateUsingUICtrl', challengeCreateUsingUICtrl);

    challengeCreateUsingUICtrl.$inject = ['utilities', '$state', '$rootScope', 'loaderService'];

    function challengeCreateUsingUICtrl(utilities, $state, $rootScope, loaderService) {
        var vm = this;
        var userKey = utilities.getData('userKey');
        vm.hostTeamId = utilities.getData('challengeHostTeamId');
        vm.challengePhase = utilities.getData('challengePhase');
        vm.challengeSplit = utilities.getData('challengeSplit');
        // vm.numberOfPhases = new Array(Integer.parseInt(vm.challengePhase));

        // start loader
        // vm.startLoader = loaderService.startLoader;

        // stop loader
        // vm.stopLoader = loaderService.stopLoader;

        vm.createChallengeUsingUI = function (challengeDetailsForm) {
            if (challengeDetailsForm) {
                // vm.startLoader('create challenge');
                var parameters = {};
                parameters.url = 'challenges/challenge/challenge_host_team/' + vm.hostTeamId +
                    '/phase/' + vm.challengePhase + '/split/' + vm.challengeSplit + '/using_ui/';
                parameters.method = 'POST';
                var formdata = new FormData();
                formdata.append("title", vm.challengeTitle);
                formdata.append("start_date", vm.challengeStartDate.toISOString());
                formdata.append("end_date", vm.challengeEndDate.toISOString());
                formdata.append("image", vm.challengeLogo);
                formdata.append("evaluation_script", vm.challengeEvaluationScript);
                parameters.data = formdata;
                parameters.token = userKey;
                parameters.callback = {
                    onSuccess: function(response) {
                        var status = response.status;
                        var details =  response.data;
                        if(status === 201) {
                            $rootScope.notify("success", details.success);
                            $state.go("home");
                        }
                    },
                    onError: function(response) {
                        // utilities.hideLoader();
                        var error = response.data;
                        $rootScope.notify("error", error);
                        // vm.stopLoader();
                    }
                };
                // utilities.showLoader();
                utilities.sendRequest(parameters, 'header', 'upload');
            }
        };
    };
})();