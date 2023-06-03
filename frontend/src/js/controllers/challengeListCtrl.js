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
        var gmtOffset = moment().utcOffset();
        var gmtSign = gmtOffset >= 0 ? '+' : '-';
        var gmtZone = 'GMT' + gmtSign + Math.abs(gmtOffset / 60);

        utilities.showLoader();
        utilities.hideButton();

        vm.currentList = [];
        vm.upcomingList = [];
        vm.pastList = [];

        vm.noneCurrentChallenge = false;
        vm.noneUpcomingChallenge = false;
        vm.nonePastChallenge = false;
        vm.getAllResults = function(parameters, resultsArray, typ){
            parameters.callback = {
                onSuccess: function(response) {
                    var data = response.data;
                    var results = data.results;
                    
                    var timezone = moment.tz.guess();
                    for (var i in results) {

                        var descLength = results[i].description.length;
                        if (descLength >= 50) {
                            results[i].isLarge = "...";
                        } else {
                            results[i].isLarge = "";
                        }

                        var offset = new Date(results[i].start_date).getTimezoneOffset();
                        results[i].start_zone = moment.tz.zone(timezone).abbr(offset);
                        offset = new Date(results[i].end_date).getTimezoneOffset();
                        results[i].end_zone = moment.tz.zone(timezone).abbr(offset);

                        var id = results[i].id;
                        vm.challengeCreator[id] = results[i].creator.id;
                        utilities.storeData("challengeCreator", vm.challengeCreator);

                        resultsArray.push(results[i]);
                    }

                    var offset = new Date(vm.currentList[i].start_date).getTimezoneOffset();
                    vm.currentList[i].start_zone = moment.tz.zone(timezone).abbr(offset);
                    vm.currentList[i].gmt_start_zone = gmtZone;
                    offset = new Date(vm.currentList[i].end_date).getTimezoneOffset();
                    vm.currentList[i].end_zone = moment.tz.zone(timezone).abbr(offset);
                    vm.currentList[i].gmt_end_zone = gmtZone;

                    var id = vm.currentList[i].id;
                    vm.challengeCreator[id] = vm.currentList[i].creator.id;
                    utilities.storeData("challengeCreator", vm.challengeCreator);
                }

                // dependent api
                // calls for upcoming challneges
                parameters.url = 'challenges/challenge/future/approved/public';
                parameters.method = 'GET';

                parameters.callback = {
                    onSuccess: function(response) {
                        var data = response.data;
                        vm.upcomingList = data.results;


                    // check for the next page
                    if (data.next !== null) {
                        var url = data.next;
                        var slicedUrl = url.substring(url.indexOf('challenges/challenge'), url.length);
                        parameters.url = slicedUrl;
                        vm.getAllResults(parameters, resultsArray);
                    } else {
                        utilities.hideLoader();
                        if (resultsArray.length === 0) {
                            vm[typ] = true;
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
                            vm.upcomingList[i].gmt_start_zone = gmtZone;
                            offset = new Date(vm.upcomingList[i].end_date).getTimezoneOffset();
                            vm.upcomingList[i].end_zone = moment.tz.zone(timezone).abbr(offset);
                            vm.upcomingList[i].gmt_end_zone = gmtZone;
                            var id = vm.upcomingList[i].id;
                            vm.challengeCreator[id] = vm.upcomingList[i].creator.id;
                            utilities.storeData("challengeCreator", vm.challengeCreator);
                            vm[typ] = false;

                        }
                    }
                },
                onError: function() {
                    utilities.hideLoader();
                }
            };


                        // dependent api
                        // calls for past challneges
                        parameters.url = 'challenges/challenge/past/approved/public';
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
                                    vm.pastList[i].gmt_start_zone = gmtZone;
                                    offset = new Date(vm.pastList[i].end_date).getTimezoneOffset();
                                    vm.pastList[i].end_zone = moment.tz.zone(timezone).abbr(offset);
                                    vm.pastList[i].gmt_end_zone = gmtZone;

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


        
        vm.challengeCreator = {};
        var parameters = {};
        if (userKey) {
            parameters.token = userKey;
        } else {
            parameters.token = null;
        }

        // calls for ongoing challenges
        parameters.url = 'challenges/challenge/present/approved/public';
        parameters.method = 'GET';
        
        vm.getAllResults(parameters, vm.currentList, "noneCurrentChallenge");
        // calls for upcoming challenges
        parameters.url = 'challenges/challenge/future/approved/public';
        parameters.method = 'GET';

        vm.getAllResults(parameters, vm.upcomingList, "noneUpcomingChallenge");

        // calls for past challenges
        parameters.url = 'challenges/challenge/past/approved/public';
        parameters.method = 'GET';

        vm.getAllResults(parameters, vm.pastList, "nonePastChallenge");

        vm.scrollUp = function() {
            angular.element($window).bind('scroll', function() {
                if (this.pageYOffset >= 100) {
                    utilities.showButton();
                } else {
                    utilities.hideButton();
                }
            });
        };
    }

})();
