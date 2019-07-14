// Invoking IIFE for challenge page
(function() {

    'use strict';
    angular
        .module('evalai')
        .controller('ChallengeListCtrl', ChallengeListCtrl);

    ChallengeListCtrl.$inject = ['utilities', '$window', 'moment'];

    function ChallengeListCtrl(utilities, $window, moment) {
        var vm = this;
        var userKey = utilities.getData('userKey');

        utilities.showLoader();

        vm.currentList = {};
        vm.upcomingList = {};
        vm.pastList = {};

        vm.noneCurrentChallenge = false;
        vm.noneUpcomingChallenge = false;
        vm.nonePastChallenge = false;

        // calls for ongoing challenges
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

                var timezone = moment.tz.guess();
                for (var i in vm.currentList) {

                    var descLength = vm.currentList[i].description.length;
                    if (descLength >= 50) {
                        vm.currentList[i].isLarge = "...";
                    } else {
                        vm.currentList[i].isLarge = "";
                    }
                    var offset = new Date(vm.currentList[i].start_date).getTimezoneOffset();
                    vm.currentList[i].start_zone = moment.tz.zone(timezone).abbr(offset);
                    offset = new Date(vm.currentList[i].end_date).getTimezoneOffset();
                    vm.currentList[i].end_zone = moment.tz.zone(timezone).abbr(offset);

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

                        var timezone = moment.tz.guess();
                        for (var i in vm.upcomingList) {

                            var descLength = vm.upcomingList[i].description.length;

                            if (descLength >= 50) {
                                vm.upcomingList[i].isLarge = "...";
                            } else {
                                vm.upcomingList[i].isLarge = "";
                            }
                            
                            var offset = new Date(vm.upcomingList[i].start_date).getTimezoneOffset();
                            vm.upcomingList[i].start_zone = moment.tz.zone(timezone).abbr(offset);
                            offset = new Date(vm.upcomingList[i].end_date).getTimezoneOffset();
                            vm.upcomingList[i].end_zone = moment.tz.zone(timezone).abbr(offset);

                            
                            var id = vm.upcomingList[i].id;
                            vm.challengeCreator[id] = vm.upcomingList[i].creator.id;
                            utilities.storeData("challengeCreator", vm.challengeCreator);
                        }

                        // dependent api
                        // calls for past challneges
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

                                var timezone = moment.tz.guess();
                                for (var i in vm.pastList) {


                                    var descLength = vm.pastList[i].description.length;
                                    if (descLength >= 50) {
                                        vm.pastList[i].isLarge = "...";
                                    } else {
                                        vm.pastList[i].isLarge = "";
                                    }

                                    var offset = new Date(vm.pastList[i].start_date).getTimezoneOffset();
                                    vm.pastList[i].start_zone = moment.tz.zone(timezone).abbr(offset);
                                    offset = new Date(vm.pastList[i].end_date).getTimezoneOffset();
                                    vm.pastList[i].end_zone = moment.tz.zone(timezone).abbr(offset);

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
