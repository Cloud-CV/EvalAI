(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('HostedChallengeCtrl', HostedChallengeCtrl);

    HostedChallengeCtrl.$inject = ['utilities'];

    function HostedChallengeCtrl(utilities) {
        var vm = this;
        var userKey = utilities.getData('userKey');

        utilities.showLoader();

        vm.myChallengeList = [];

        vm.noneMyChallenges = false;

        var parameters = {};
        parameters.url = 'hosts/challenge_host_team/';
        parameters.method = 'GET';
        parameters.token = userKey;
        parameters.callback = {
            onSuccess: function(response) {
                var participant_host_team = response["data"]["results"];
                parameters.method = 'GET';
                for (var i=0; i<participant_host_team.length; i++) {
                    parameters.url = "challenges/challenge_host_team/" + participant_host_team[i]["id"] + "/challenge";
                    parameters.callback = {
                        onSuccess: function(response) {
                            var data = response.data;
                            for (var j=0; j<data.results.length; j++){
                                vm.myChallengeList.push(data.results[j]);
                            }
                        },
                        onError: function() {
                            utilities.hideLoader();
                        }
                    };
                    utilities.sendRequest(parameters);
                }
                console.log(vm.myChallengeList);
                if (vm.noneMyChallenges.length === 0) {
                    vm.noneMyChallenges = true;
                } else {
                    vm.noneMyChallenges = false;
                }
                utilities.hideLoader();
            },
            onError: function() {
                utilities.hideLoader();
            }
        };
        utilities.sendRequest(parameters);
    }
})();