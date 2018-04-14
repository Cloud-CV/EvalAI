// Invoking IIFE for challenge page
(function() {

    'use strict';
    angular
        .module('evalai')
        .controller('ChallengeListCtrl', ChallengeListCtrl);

    ChallengeListCtrl.$inject = ['utilities', '$window'];

    function ChallengeListCtrl(utilities, $window) {
        var vm = this;
        var userKey = utilities.getData('userKey');

        utilities.showLoader();

        vm.myChallengeList = [];
        vm.currentList = {};
        vm.upcomingList = {};
        vm.pastList = {};

        vm.noneMyChallenges = false;
        vm.noneCurrentChallenge = false;
        vm.noneUpcomingChallenge = false;
        vm.nonePastChallenge = false;

        // calls for ongoing challneges
        vm.challengeCreator = {};
        var parameters = {};
        parameters.method = 'GET';
        if (userKey) {
            parameters.token = userKey;
        } else {
            parameters.token = null;
        }
        parameters.url = 'challenges/challenge/present';

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

                    var id = vm.currentList[i].id;
                    vm.challengeCreator[id] = vm.currentList[i].creator.id;
                    utilities.storeData("challengeCreator", vm.challengeCreator);
                }

                // dependent api
                // calls for upcoming challneges
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

                            var id = vm.upcomingList[i].id;
                            vm.challengeCreator[id] = vm.upcomingList[i].creator.id;
                            utilities.storeData("challengeCreator", vm.challengeCreator);
                        }

                        // dependent api
                        // calls for upcoming challneges
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
                                    var id = vm.pastList[i].id;
                                    vm.challengeCreator[id] = vm.pastList[i].creator.id;
                                    utilities.storeData("challengeCreator", vm.challengeCreator);
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

        vm.scrollUp = function() {
            utilities.hideButton();
            angular.element($window).bind('scroll', function() {
                if (this.pageYoffset >= 100) {
                    utilities.showButton();
                } else {
                    utilities.hideButton();
                }
            });
        };

        parameters = {};
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

            },
            onError: function() {
                utilities.hideLoader();
            }
        };

        utilities.sendRequest(parameters);

    }

})();
