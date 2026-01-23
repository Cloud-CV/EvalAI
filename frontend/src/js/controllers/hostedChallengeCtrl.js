(function () {

    'use strict';

    angular
        .module('evalai')
        .controller('HostedChallengesCtrl', HostedChallengesCtrl);

    HostedChallengesCtrl.$inject = ['utilities'];

    function HostedChallengesCtrl(utilities) {
        var vm = this;
        var userKey = utilities.getData('userKey');

        utilities.showLoader();
        var gmtOffset = moment().utcOffset();
        var gmtSign = gmtOffset >= 0 ? '+' : '-';
        var gmtHours = Math.abs(Math.floor(gmtOffset / 60));
        var gmtMinutes = Math.abs(gmtOffset % 60);
        var gmtZone = 'GMT ' + gmtSign + ' ' + gmtHours + ':' + (gmtMinutes < 10 ? '0' : '') + gmtMinutes;

        vm.challengeList = [];
        vm.ongoingChallenges = [];
        vm.upcomingChallenges = [];
        vm.pastChallenges = [];
        vm.challengeCreator = {};

        vm.currentTab = 'ongoing';

        vm.setCurrentTab = function (tabName) {
            vm.currentTab = tabName;
        };

        // Use separate parameter object to avoid race conditions
        var hostTeamParams = {
            url: 'hosts/challenge_host_team/',
            method: 'GET',
            token: userKey,
            callback: {
                onSuccess: function (response) {
                    var host_teams = response["data"]["results"];
                    var timezone = moment.tz.guess();
                    
                    // Create separate parameter objects for each host team request
                    for (var i = 0; i < host_teams.length; i++) {
                        // Use IIFE to capture loop variable
                        (function(hostTeamId) {
                            var challengeParams = {
                                url: "challenges/challenge_host_team/" + hostTeamId + "/challenge",
                                method: 'GET',
                                token: userKey,
                                callback: {
                                    onSuccess: function (response) {
                                        var data = response.data;
                                        var current = new Date();
                                        for (var j = 0; j < data.results.length; j++) {
                                            var challenge = data.results[j];
                                            vm.challengeList.push(challenge);
                                            var id = challenge.id;
                                            vm.challengeCreator[id] = challenge.creator.id;
                                            utilities.storeData("challengeCreator", vm.challengeCreator);
                                            var offset = new Date(challenge.start_date).getTimezoneOffset();
                                            challenge.time_zone = moment.tz.zone(timezone).abbr(offset);
                                            challenge.gmt_zone = gmtZone;

                                            var startDate = new Date(challenge.start_date);
                                            var endDate = new Date(challenge.end_date);

                                            if (startDate > current) {
                                                if (!vm.upcomingChallenges.some(function(c) { return c.id === challenge.id })) {
                                                    vm.upcomingChallenges.push(challenge);
                                                }
                                            }
                                            else if (current >= startDate && current <= endDate) {
                                                if (!vm.ongoingChallenges.some(function(c) { return c.id === challenge.id })) {
                                                    vm.ongoingChallenges.push(challenge);
                                                }
                                            }
                                            else if (current > endDate) {
                                                if (!vm.pastChallenges.some(function(c) { return c.id === challenge.id })) {
                                                    vm.pastChallenges.push(challenge);
                                                }
                                            }
                                        }
                                    },
                                    onError: function () {
                                        utilities.hideLoader();
                                    }
                                }
                            };
                            utilities.sendRequest(challengeParams);
                        })(host_teams[i]["id"]);
                    }
                    utilities.hideLoader();
                },
                onError: function () {
                    utilities.hideLoader();
                }
            }
        };
        utilities.sendRequest(hostTeamParams);
    }
})();
