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
        utilities.hideButton();

        vm.currentList = [];
        vm.upcomingList = [];
        vm.pastList = [];

        vm.noneCurrentChallenge = true;
        vm.noneUpcomingChallenge = true;
        vm.nonePastChallenge = true;
        vm.getAllResults = function(parameters, resultsArray){
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

                    // check for the next page
                    if (data.next !== null) {
                        var url = data.next;
                        var slicedUrl = url.substring(url.indexOf('challenges/challenge'), url.length);
                        parameters.url = slicedUrl;
                        vm.getAllResults(parameters, resultsArray);
                    } else {
                        utilities.hideLoader();
                    }
                },
                onError: function() {
                    utilities.hideLoader();
                }
            };

            utilities.sendRequest(parameters);
        };

        
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
        
        vm.getAllResults(parameters, vm.currentList);

        if (vm.currentList.length === 0) {
            vm.noneCurrentChallenge = true;
        } else {
            vm.noneCurrentChallenge = false;
        }

        // calls for upcoming challenges
        parameters.url = 'challenges/challenge/future/approved/public';
        parameters.method = 'GET';

        vm.getAllResults(parameters, vm.upcomingList);

        if (vm.upcomingList.length === 0) {
            vm.noneUpcomingChallenge = true;
        } else {
            vm.noneUpcomingChallenge = false;
        }

        // calls for past challenges
        parameters.url = 'challenges/challenge/past/approved/public';
        parameters.method = 'GET';

        vm.getAllResults(parameters, vm.pastList);

        if (vm.pastList.length === 0) {
            vm.nonePastChallenge = true;
        } else {
            vm.nonePastChallenge = false;
        }

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
