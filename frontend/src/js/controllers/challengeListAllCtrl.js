// Invoking IIFE for challenge page
(function() {

    'use strict';
    angular
        .module('evalai')
        .controller('ChallengeListAllCtrl', ChallengeListAllCtrl);

    ChallengeListAllCtrl.$inject = ['utilities'];

    function ChallengeListAllCtrl(utilities) {
        var vm = this;

        vm.currentList = {};
        vm.upcomingList = {};
        vm.pastList = {};

        vm.noneCurrentChallenge = false;
        vm.noneUpcomingChallenge = false;
        vm.nonePastChallenge = false;

        // calls for ongoing challneges
        var parameters = {};
        parameters.url = 'challenges/challenge/present';
        parameters.method = 'GET';

        parameters.callback = {
            onSuccess: function(response) {
                var data = response.data;
                vm.currentList = data.results;

                if (vm.currentList.length === 0) {
                    vm.noneCurrentChallenge = true;
                } else {
                    vm.noneCurrentChallenge = false;
                }

                for (var i in vm.currentList) {
                    var descLength = vm.currentList[i].description.length;
                    if (descLength >= 50) {
                        vm.currentList[i].isLarge = "...";
                    } else {
                        vm.currentList[i].isLarge = "";
                    }
                }

                // API call to fetch future challenges
                var parameters = {};
                parameters.url = 'challenges/challenge/future';
                parameters.method = 'GET';

                parameters.callback = {
                    onSuccess: function(response) {
                        var data = response.data;
                        vm.upcomingList = data.results;

                        if (vm.upcomingList.length === 0) {
                            vm.noneUpcomingChallenge = true;
                        } else {
                            vm.noneUpcomingChallenge = false;
                        }

                        for (var i in vm.upcomingList) {
                            var descLength = vm.upcomingList[i].description.length;
                            if (descLength >= 50) {
                                vm.upcomingList[i].isLarge = "...";
                            } else {
                                vm.upcomingList[i].isLarge = "";
                            }
                        }

                        // API call to fetch past challenges
                        var parameters = {};
                        parameters.url = 'challenges/challenge/past';
                        parameters.method = 'GET';
                        parameters.callback = {
                            onSuccess: function(response) {
                                var data = response.data;
                                vm.pastList = data.results;

                                if (vm.pastList.length === 0) {
                                    vm.nonePastChallenge = true;
                                } else {
                                    vm.nonePastChallenge = false;
                                }

                                for (var i in vm.pastList) {
                                    var descLength = vm.pastList[i].description.length;
                                    if (descLength >= 50) {
                                        vm.pastList[i].isLarge = "...";
                                    } else {
                                        vm.pastList[i].isLarge = "";
                                    }
                                }

                                utilities.hideLoader();
                            },
                            onError: function() {
                                utilities.hideLoader();
                            }
                        };
                        utilities.sendRequest(parameters);
                    },
                    onError: function() {
                        utilities.hideLoader();
                    }
                };
                utilities.sendRequest(parameters);
            },
            onError: function() {

                utilities.hideLoader();
            }
        };
        utilities.sendRequest(parameters);
    }
})();
