// Invoking IIFE for challenge page
(function () {
    'use strict';

    angular
        .module('evalai')
        .controller('ChallengeListCtrl', ChallengeListCtrl);

    ChallengeListCtrl.$inject = ['utilities', '$window', 'moment', '$scope', '$timeout'];

    function ChallengeListCtrl(utilities, $window, moment, $scope, $timeout) {
        var vm = this;
        var userKey = utilities.getData('userKey');
        var gmtOffset = moment().utcOffset();
        var gmtSign = gmtOffset >= 0 ? '+' : '-';
        var gmtHours = Math.abs(Math.floor(gmtOffset / 60));
        var gmtMinutes = Math.abs(gmtOffset % 60);
        var gmtZone = 'GMT ' + gmtSign + ' ' + gmtHours + ':' + (gmtMinutes < 10 ? '0' : '') + gmtMinutes;

        // Initializing the loader
        utilities.showLoader();
        utilities.hideButton();

        // Initialize variables
        vm.currentList = [];
        vm.upcomingList = [];
        vm.pastList = [];
        vm.filteredChallenges = [];
        vm.challengeCreator = {};

        // Flags for empty lists
        vm.noneCurrentChallenge = false;
        vm.noneUpcomingChallenge = false;
        vm.nonePastChallenge = false;

        // Filter variables
        vm.searchQuery = '';
        vm.isFilterVisible = false;
        vm.filter = {
            organization: '',
            tags: '',
            sortByStartDate: false,
            sortByEndDate: false
        };

        // Toggle filter panel visibility
        vm.toggleFilterPanel = function() {
            vm.isFilterVisible = !vm.isFilterVisible;
            // Force digest cycle to ensure UI updates
            if (!$scope.$$phase) {
                $scope.$apply();
            }
        };

        // Function to retrieve challenge data from API
        vm.getAllResults = function (parameters, resultsArray, type) {
            parameters.method = 'GET';
            parameters.callback = {
                onSuccess: function (response) {
                    if (!response || !response.data) {
                        utilities.hideLoader();
                        return;
                    }

                    var data = response.data;
                    var results = data.results || [];

                    var timezone = moment.tz.guess();
                    results.forEach(function (challenge) {
                        if (!challenge || !challenge.description) {
                            return;
                        }

                        var descLength = challenge.description.length;
                        challenge.isLarge = descLength >= 50 ? '...' : '';

                        var offset = new Date(challenge.start_date).getTimezoneOffset();
                        challenge.time_zone = moment.tz.zone(timezone).abbr(offset);
                        challenge.gmt_zone = gmtZone;

                        // Convert dates to Date objects for easier comparison
                        challenge.start_date_obj = new Date(challenge.start_date);
                        challenge.end_date_obj = new Date(challenge.end_date);

                        var id = challenge.id;
                        if (id && challenge.creator && challenge.creator.id) {
                            vm.challengeCreator[id] = challenge.creator.id;
                            utilities.storeData("challengeCreator", vm.challengeCreator);
                        }

                        resultsArray.push(challenge);
                    });

                    if (data.next !== null) {
                        var url = data.next;
                        var slicedUrl = url.substring(url.indexOf('challenges/challenge'));
                        parameters.url = slicedUrl;
                        vm.getAllResults(parameters, resultsArray, type);
                    } else {
                        // Sort challenges by start date by default
                        resultsArray.sort(function(a, b) {
                            return a.start_date_obj - b.start_date_obj;
                        });

                        $timeout(function() {
                            utilities.hideLoader();
                            vm[type] = resultsArray.length === 0;

                            if (!$scope.$$phase) {
                                $scope.$apply();
                            }
                        });
                    }
                },
                onError: function () {
                    utilities.hideLoader();
                    vm.errorMessage = "Failed to load challenges. Please try again later.";

                    if (!$scope.$$phase) {
                        $scope.$apply();
                    }
                }
            };
            utilities.sendRequest(parameters);
        };

        // Initialize challenges
        var parameters = { token: userKey ? userKey : null };

        parameters.url = 'challenges/challenge/present/approved/public';
        vm.getAllResults(parameters, vm.currentList, 'noneCurrentChallenge');

        parameters.url = 'challenges/challenge/future/approved/public';
        vm.getAllResults(parameters, vm.upcomingList, 'noneUpcomingChallenge');

        parameters.url = 'challenges/challenge/past/approved/public';
        vm.getAllResults(parameters, vm.pastList, 'nonePastChallenge');

        // Apply filters on challenges - Fixed implementation
        vm.applyFilter = function () {
            vm.hasAppliedFilter = true;

            // Handle empty list case
            if (!vm.currentList || vm.currentList.length === 0) {
                vm.filteredChallenges = [];
                return;
            }

            // Start with a copy of the current list
            vm.filteredChallenges = angular.copy(vm.currentList);

            // Perform filtering
            vm.filteredChallenges = vm.filteredChallenges.filter(function (challenge) {
                var match = true;
                var filterResults = { passed: true, reasons: [] };

                // Organization filter
                if (vm.filter.organization && vm.filter.organization.trim() !== '') {
                    if (!challenge.creator || !challenge.creator.team_name ||
                        !challenge.creator.team_name.toLowerCase().includes(vm.filter.organization.toLowerCase())) {
                        match = false;
                        filterResults.passed = false;
                        filterResults.reasons.push('Organization mismatch');
                    }
                }

                // Tags filter
                if (vm.filter.tags && vm.filter.tags.trim() !== '') {
                    var tagMatch = false;
                    var searchTags = vm.filter.tags.toLowerCase().split(',');

                    if (challenge.list_tags && challenge.list_tags.length > 0) {
                        searchTags.forEach(function(searchTag) {
                            searchTag = searchTag.trim();
                            if (searchTag === '') return;

                            challenge.list_tags.forEach(function(challengeTag) {
                                if (challengeTag.toLowerCase().includes(searchTag)) {
                                    tagMatch = true;
                                }
                            });
                        });

                        if (!tagMatch) {
                            match = false;
                            filterResults.passed = false;
                            filterResults.reasons.push('Tag mismatch');
                        }
                    } else {
                        match = false; // No tags to match against
                        filterResults.passed = false;
                        filterResults.reasons.push('Challenge has no tags');
                    }
                }

                return match;
            });

            // Apply sorting based on checkboxes
            applySorting(vm.filteredChallenges);

            // Ensure UI updates
            if (!$scope.$$phase) {
                $scope.$apply();
            }
        };

        // Helper function to apply sorting based on current checkbox states
        function applySorting(challengeList) {
            // First priority: Sort by start date
            if (vm.filter.sortByStartDate) {
                challengeList.sort(function(a, b) {
                    return a.start_date_obj - b.start_date_obj;
                });
            }

            // Second priority: Sort by end date (overrides start date sort if both are selected)
            if (vm.filter.sortByEndDate) {
                challengeList.sort(function(a, b) {
                    return a.end_date_obj - b.end_date_obj;
                });
            }

            // If no sort option is selected, default to start date
            if (!vm.filter.sortByStartDate && !vm.filter.sortByEndDate) {
                challengeList.sort(function(a, b) {
                    return a.start_date_obj - b.start_date_obj;
                });
            }
        }

        // Reset all filters
        vm.resetFilters = function() {
            vm.filter = {
                organization: '',
                tags: '',
                sortByStartDate: false,
                sortByEndDate: false
            };
            vm.filteredChallenges = [];
            vm.hasAppliedFilter = false;

            // Ensure UI updates
            if (!$scope.$$phase) {
                $scope.$apply();
            }
        };

        // Initialize hasAppliedFilter flag
        vm.hasAppliedFilter = false;

        // Scroll up button visibility
        vm.scrollUp = function () {
            angular.element($window).bind('scroll', function () {
                if (this.pageYOffset >= 100) {
                    utilities.showButton();
                } else {
                    utilities.hideButton();
                }
            });
        };

        // Initialize the controller
        function init() {
            vm.isFilterVisible = false; // Ensure filter panel is hidden initially
        }

        // Call init
        init();
    }
})();
