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
        
        // Pre-compute timezone info once (not per-result)
        var gmtOffset = moment().utcOffset();
        var gmtSign = gmtOffset >= 0 ? '+' : '-';
        var gmtHours = Math.abs(Math.floor(gmtOffset / 60));
        var gmtMinutes = Math.abs(gmtOffset % 60);
        var gmtZone = 'GMT ' + gmtSign + ' ' + gmtHours + ':' + (gmtMinutes < 10 ? '0' : '') + gmtMinutes;
        var timezone = moment.tz.guess();
        var tzZone = moment.tz.zone(timezone);

        utilities.showLoader();
        utilities.hideButton();

        vm.currentList = [];
        vm.upcomingList = [];
        vm.pastList = [];

        vm.noneCurrentChallenge = false;
        vm.noneUpcomingChallenge = false;
        vm.nonePastChallenge = false;
        vm.challengeCreator = {};

        // Track pending category fetches to hide loader only when all complete
        var pendingCategories = 3;
        var checkAllComplete = function() {
            pendingCategories--;
            if (pendingCategories === 0) {
                // Store challenge creators once after all fetches complete
                utilities.storeData("challengeCreator", vm.challengeCreator);
                utilities.hideLoader();
            }
        };

        // Process results batch efficiently
        var processResults = function(results) {
            for (var i = 0, len = results.length; i < len; i++) {
                var challenge = results[i];
                
                // Set description truncation flag
                challenge.isLarge = challenge.description.length >= 50 ? "..." : "";
                
                // Set timezone info using pre-computed values
                var offset = new Date(challenge.start_date).getTimezoneOffset();
                challenge.time_zone = tzZone.abbr(offset);
                challenge.gmt_zone = gmtZone;
                
                // Track creator
                vm.challengeCreator[challenge.id] = challenge.creator.id;
            }
            return results;
        };

        vm.getAllResults = function(parameters, resultsArray, typ) {
            parameters.method = 'GET';
            parameters.callback = {
                onSuccess: function(response) {
                    var data = response.data;
                    var results = data.results;
                    
                    // Process and add results in batch
                    var processed = processResults(results);
                    Array.prototype.push.apply(resultsArray, processed);

                    // Check for next page
                    if (data.next !== null) {
                        var url = data.next;
                        parameters.url = url.substring(url.indexOf('challenges/challenge'), url.length);
                        vm.getAllResults(parameters, resultsArray, typ);
                    } else {
                        // This category is complete
                        vm[typ] = resultsArray.length === 0;
                        checkAllComplete();
                    }
                },
                onError: function() {
                    vm[typ] = true;
                    checkAllComplete();
                }
            };

            utilities.sendRequest(parameters);
        };

        var token = userKey ? userKey : null;

        // Fire all three category fetches in parallel
        var ongoingParams = { token: token, url: 'challenges/challenge/present/approved/public' };
        var upcomingParams = { token: token, url: 'challenges/challenge/future/approved/public' };
        var pastParams = { token: token, url: 'challenges/challenge/past/approved/public' };

        vm.getAllResults(ongoingParams, vm.currentList, "noneCurrentChallenge");
        vm.getAllResults(upcomingParams, vm.upcomingList, "noneUpcomingChallenge");
        vm.getAllResults(pastParams, vm.pastList, "nonePastChallenge");

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

