// Invoking IIFE for challenge page
(function() {

    'use strict';
    angular
        .module('evalai')
        .controller('ChallengeListCtrl', ChallengeListCtrl);

    ChallengeListCtrl.$inject = ['utilities', '$window', 'moment'];

    function ChallengeListCtrl(utilities, $window, moment) {
        var vm = this;
        var gmtOffset = moment().utcOffset();
        var gmtSign = gmtOffset >= 0 ? '+' : '-';
        var gmtHours = Math.abs(Math.floor(gmtOffset / 60));
        var gmtMinutes = Math.abs(gmtOffset % 60);
        var gmtZone = 'GMT ' + gmtSign + ' ' + gmtHours + ':' + (gmtMinutes < 10 ? '0' : '') + gmtMinutes;

        utilities.showLoader();
        utilities.hideButton();

        vm.currentList = [];
        vm.upcomingList = [];
        vm.pastList = [];

        // Total counts from API (shown immediately, before all pages load)
        vm.currentCount = 0;
        vm.upcomingCount = 0;
        vm.pastCount = 0;

        vm.noneCurrentChallenge = false;
        vm.noneUpcomingChallenge = false;
        vm.nonePastChallenge = false;
        vm.challengeCreator = {};

        vm.getAllResults = function(parameters, resultsArray, typ, countKey, isFirstPage){
            parameters.method = 'GET';
            parameters.callback = {
                onSuccess: function(response) {
                    var data = response.data;
                    var results = data.results;

                    // Set the total count from API on first page
                    if (isFirstPage && countKey && data.count !== undefined) {
                        vm[countKey] = data.count;
                    }
                    
                    var timezone = moment.tz.guess();
                    for (var i in results) {

                        var descLength = results[i].description.length;
                        if (descLength >= 50) {
                            results[i].isLarge = "...";
                        } else {
                            results[i].isLarge = "";
                        }

                        var offset = new Date(results[i].start_date).getTimezoneOffset();
                        results[i].time_zone = moment.tz.zone(timezone).abbr(offset);
                        results[i].gmt_zone = gmtZone;

                        var id = results[i].id;
                        vm.challengeCreator[id] = results[i].creator.id;
                        utilities.storeData("challengeCreator", vm.challengeCreator);

                        resultsArray.push(results[i]);
                    }

                    // check for the next page
                    if (data.next !== null) {
                        var url = data.next;
                        var slicedUrl = url.substring(url.indexOf('challenges/challenge'), url.length);
                        // Create a new parameters object to avoid race conditions
                        // Don't pass token for public endpoints
                        var nextParams = {
                            url: slicedUrl
                        };
                        vm.getAllResults(nextParams, resultsArray, typ, countKey, false);
                    } else {
                        utilities.hideLoader();
                        if (resultsArray.length === 0) {
                            vm[typ] = true;
                        } else {
                            vm[typ] = false;
                        }
                    }
                },
                onError: function() {
                    utilities.hideLoader();
                }
            };

            utilities.sendRequest(parameters);
        };

        // Create separate parameter objects for each API call to avoid race conditions
        // These are public endpoints, so don't send token (avoids errors with stale tokens after logout)
        var currentParams = {
            url: 'challenges/challenge/present/approved/public'
        };
        var upcomingParams = {
            url: 'challenges/challenge/future/approved/public'
        };
        var pastParams = {
            url: 'challenges/challenge/past/approved/public'
        };

        // calls for ongoing challenges
        vm.getAllResults(currentParams, vm.currentList, "noneCurrentChallenge", "currentCount", true);
        // calls for upcoming challenges
        vm.getAllResults(upcomingParams, vm.upcomingList, "noneUpcomingChallenge", "upcomingCount", true);
        // calls for past challenges
        vm.getAllResults(pastParams, vm.pastList, "nonePastChallenge", "pastCount", true);

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

