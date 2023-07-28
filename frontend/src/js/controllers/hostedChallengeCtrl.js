(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('HostedChallengesCtrl', HostedChallengesCtrl);

    HostedChallengesCtrl.$inject = ['utilities', '$rootScope'];

    function HostedChallengesCtrl(utilities, $rootScope) {
        var vm = this;
        var userKey = utilities.getData('userKey');

        utilities.showLoader();
        var gmtOffset = moment().utcOffset();
        var gmtSign = gmtOffset >= 0 ? '+' : '-';
        var gmtHours = Math.abs(Math.floor(gmtOffset / 60));
        var gmtMinutes = Math.abs(gmtOffset % 60);
        var gmtZone = 'GMT ' + gmtSign + ' ' + gmtHours + ':' + (gmtMinutes < 10 ? '0' : '') + gmtMinutes;

        vm.challengeList = [];
        vm.challengeCreator = {};
        vm.searchTitle = [];
        vm.selecteddomain = [];

        var parameters = {};
        parameters.url = 'hosts/challenge_host_team/';
        parameters.method = 'GET';
        parameters.token = userKey;
        parameters.callback = {
            onSuccess: function(response) {
                var host_teams = response["data"]["results"];
                parameters.method = 'GET';
                var timezone = moment.tz.guess();
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
                                var offset = new Date(data.results[j].start_date).getTimezoneOffset();
                                vm.challengeList[j].time_zone = moment.tz.zone(timezone).abbr(offset);
                                vm.challengeList[j].gmt_zone = gmtZone;
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

        parameters.url = "challenges/challenge/get_domain_choices/";
        parameters.method = 'GET';
        parameters.data = {};
        parameters.callback = {
            onSuccess: function(response) {
                vm.domain_choices = response.data;
            },
            onError: function(response) {
                var error = response.data;
                $rootScope.notify("error", error);
            }
        };
        utilities.sendRequest(parameters);
    }
})();
