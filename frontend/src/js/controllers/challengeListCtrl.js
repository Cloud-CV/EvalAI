(function () {
    'use strict';

    angular
        .module('evalai')
        .controller('ChallengeListCtrl', ChallengeListCtrl);

    ChallengeListCtrl.$inject = ['utilities', '$window', 'moment', '$scope'];

    function ChallengeListCtrl(utilities, $window, moment, $scope) {
        var vm = this;
        var userKey = utilities.getData('userKey');
        var gmtOffset = moment().utcOffset();
        var gmtSign = gmtOffset >= 0 ? '+' : '-';
        var gmtHours = Math.abs(Math.floor(gmtOffset / 60));
        var gmtMinutes = Math.abs(gmtOffset % 60);
        var gmtZone = 'GMT ' + gmtSign + ' ' + gmtHours + ':' + (gmtMinutes < 10 ? '0' : '') + gmtMinutes;

        utilities.showLoader();
        utilities.hideButton();

        // Initialize lists
        vm.currentList = [];
        vm.upcomingList = [];
        vm.pastList = [];

        // Flags for "None" cases
        vm.noneCurrentChallenge = false;
        vm.noneUpcomingChallenge = false;
        vm.nonePastChallenge = false;

        // Function to fetch challenge results
        vm.getAllResults = function (parameters, resultsArray, flagType) {
            parameters.callback = {
                onSuccess: function (response) {
                    var data = response.data;
                    var results = data.results;
                    var timezone = moment.tz.guess();

                    results.forEach(function (challenge) {
                        challenge.isLarge = challenge.description.length >= 50 ? "..." : "";

                        var offset = new Date(challenge.start_date).getTimezoneOffset();
                        challenge.time_zone = moment.tz.zone(timezone).abbr(offset);
                        challenge.gmt_zone = gmtZone;

                        vm.challengeCreator[challenge.id] = challenge.creator.id;
                        utilities.storeData("challengeCreator", vm.challengeCreator);

                        resultsArray.push(challenge);
                    });

                    if (data.next !== null) {
                        parameters.url = data.next.substring(data.next.indexOf('challenges/challenge'));
                        vm.getAllResults(parameters, resultsArray, flagType);
                    } else {
                        utilities.hideLoader();
                        vm[flagType] = resultsArray.length === 0;
                    }
                },
                onError: function () {
                    utilities.hideLoader();
                }
            };

            utilities.sendRequest(parameters);
        };

        vm.challengeCreator = {};
        var parameters = userKey ? { token: userKey } : { token: null };

        // Scroll button functionality
        vm.scrollUp = function () {
            angular.element($window).bind('scroll', function () {
                this.pageYOffset >= 100 ? utilities.showButton() : utilities.hideButton();
            });
        };

        vm.switchTab = function (tab) {

            // Remove active classes from all buttons and content

            angular.element('.tab-content').removeClass('active');
            angular.element('.tab-button').removeClass('active');
        
            // Add active class to the selected tab content
            angular.element('#' + tab).addClass('active');
        
            // Find the clicked button using button text
            angular.element('.tab-button').each(function () {
                if (angular.element(this).text().trim() === tab.charAt(0).toUpperCase() + tab.slice(1) + ' Challenges') {
                    angular.element(this).addClass('active');
                }
            });
        
            // Force UI update in case AngularJS misses it
            if (!$scope.$$phase) {
                $scope.$apply();
            }
        
            // Fetch data if not already loaded
            if (tab === 'ongoing' && vm.currentList.length === 0) {
                vm.getAllResults({ url: 'challenges/challenge/present/approved/public', method: 'GET' }, vm.currentList, "noneCurrentChallenge");
            } else if (tab === 'upcoming' && vm.upcomingList.length === 0) {
                vm.getAllResults({ url: 'challenges/challenge/future/approved/public', method: 'GET' }, vm.upcomingList, "noneUpcomingChallenge");
            } else if (tab === 'past' && vm.pastList.length === 0) {
                vm.getAllResults({ url: 'challenges/challenge/past/approved/public', method: 'GET' }, vm.pastList, "nonePastChallenge");
            }
        };
        

        // Initialize with the default tab
        $scope.$evalAsync(function () {
            vm.switchTab('ongoing');
        });
        
    }
})();
