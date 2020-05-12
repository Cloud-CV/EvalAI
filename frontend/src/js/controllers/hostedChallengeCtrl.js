(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('HostedChallengesCtrl', HostedChallengesCtrl);

    HostedChallengesCtrl.$inject = ['utilities'];

    function HostedChallengesCtrl(utilities) {
        var vm = this;
        var userKey = utilities.getData('userKey');

        utilities.showLoader();

        vm.challengeList = [];
        vm.challengeCreator = {};

        var parameters = {};
        parameters.url = 'hosts/challenge_host_team/';
        parameters.method = 'GET';
        parameters.token = userKey;
        parameters.callback = {
            onSuccess: function(response) {
                var host_teams = response["data"]["results"];
                parameters.method = 'GET';
                for (var i=0; i<host_teams.length; i++) {
                    parameters.url = "challenges/challenge_host_team/" + host_teams[i]["id"] + "/challenge";
                    parameters.callback = {
                        onSuccess: function(response) {
                            var data = response.data;
                            for (var j=0; j<data.results.length; j++){
                                vm.challengeList.push(data.results[j]);
                                var id = data.results[j].id;
                                vm.challengeCreator[id] = data.results[j].creator.id;
                                utilities.storeData("challengeCreator", vm.challengeCreator);
                            }
                        },
                        onError: function() {
                            utilities.hideLoader();
                        }
                    };
                    utilities.sendRequest(parameters);
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
