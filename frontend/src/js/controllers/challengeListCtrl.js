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

        vm.currentList = {};
        vm.upcomingList = {};
        vm.pastList = {};

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

                    vm.currentList[i].start_date = strftime('%b %d, %Y %H:%M:%S %Z', new Date(vm.currentList[i].start_date));
                    vm.currentList[i].end_date = strftime('%b %d, %Y %H:%M:%S %Z', new Date(vm.currentList[i].end_date));

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

                            vm.upcomingList[i].start_date = strftime('%b %d, %Y %H:%M:%S %Z', new Date(vm.upcomingList[i].start_date));
                            vm.upcomingList[i].end_date = strftime('%b %d, %Y %H:%M:%S %Z', new Date(vm.upcomingList[i].end_date));

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

                                    vm.pastList[i].start_date = strftime('%b %d, %Y %H:%M:%S %Z', new Date(vm.pastList[i].start_date));
                                    vm.pastList[i].end_date = strftime('%b %d, %Y %H:%M:%S %Z', new Date(vm.pastList[i].end_date));

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
    }

})();
