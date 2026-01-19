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

    
        utilities.showLoader();
        utilities.hideButton();

        
        vm.currentList = [];
        vm.upcomingList = [];
        vm.pastList = [];
        vm.challengeCreator = {};

        
        vm.filteredCurrentList = [];
        vm.filteredUpcomingList = [];
        vm.filteredPastList = [];

        
        vm.noneCurrentChallenge = false;
        vm.noneUpcomingChallenge = false;
        vm.nonePastChallenge = false;

        
        vm.searchQuery = '';
        vm.isFilterVisible = false;
        vm.filter = {
            organization: '',
            tags: '',
            sortByStartDate: false,
            sortByEndDate: false
        };

        
        vm.toggleFilterPanel = function () {
            vm.isFilterVisible = !vm.isFilterVisible;
            if (!$scope.$$phase) {
                $scope.$apply();
            }
        };

        
        vm.getAllResults = function (parameters, resultsArray, type) {
            parameters.method = 'GET';
            parameters.callback = {
                onSuccess: function (response) {
                    if (!response || !response.data || !response.data.results) {
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
                        resultsArray.sort(function (a, b) {
                            return a.start_date_obj - b.start_date_obj;
                        });

                        $timeout(function () {
                            utilities.hideLoader();
                            vm[type] = resultsArray.length === 0;

                            
                            if (type === 'noneCurrentChallenge') {
                                vm.filteredCurrentList = angular.copy(resultsArray);
                            } else if (type === 'noneUpcomingChallenge') {
                                vm.filteredUpcomingList = angular.copy(resultsArray);
                            } else if (type === 'nonePastChallenge') {
                                vm.filteredPastList = angular.copy(resultsArray);
                            }

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

        
        var parameters = { token: userKey ? userKey : null };

        parameters.url = 'challenges/challenge/present/approved/public';
        vm.getAllResults(parameters, vm.currentList, 'noneCurrentChallenge');

        parameters.url = 'challenges/challenge/future/approved/public';
        vm.getAllResults(parameters, vm.upcomingList, 'noneUpcomingChallenge');

        parameters.url = 'challenges/challenge/past/approved/public';
        vm.getAllResults(parameters, vm.pastList, 'nonePastChallenge');

        
        function filterChallenges(challengeList) {
            if (!challengeList || challengeList.length === 0) {
                return [];
            }

            var filtered = angular.copy(challengeList);

            if (vm.filter.organization && vm.filter.organization.trim() !== '') {
                filtered = filtered.filter(function (challenge) {
                    return challenge.creator &&
                        challenge.creator.team_name &&
                        challenge.creator.team_name.toLowerCase().includes(vm.filter.organization.toLowerCase());
                });
            }

            if (vm.filter.tags && vm.filter.tags.trim() !== '') {
                filtered = filtered.filter(function (challenge) {
                    var tagMatch = false;
                    var searchTags = vm.filter.tags.toLowerCase().split(',');

                    if (challenge.list_tags && challenge.list_tags.length > 0) {
                        searchTags.forEach(function (searchTag) {
                            searchTag = searchTag.trim();
                            if (searchTag === '') return;

                            challenge.list_tags.forEach(function (challengeTag) {
                                if (challengeTag.toLowerCase().includes(searchTag)) {
                                    tagMatch = true;
                                }
                            });
                        });
                        return tagMatch;
                    } else {
                        return false;
                    }
                });
            }

            applySorting(filtered);
            return filtered;
        }

        // Apply filters on all challenge lists
        vm.applyFilter = function () {
            vm.hasAppliedFilter = true;

            // Apply filters to all three challenge lists
            vm.filteredCurrentList = filterChallenges(vm.currentList);
            vm.filteredUpcomingList = filterChallenges(vm.upcomingList);
            vm.filteredPastList = filterChallenges(vm.pastList);

            if (!$scope.$$phase) {
                $scope.$apply();
            }
        };

        // Helper function for sorting
        function applySorting(challengeList) {
            if (vm.filter.sortByEndDate) {
                challengeList.sort(function (a, b) {
                    return a.end_date_obj - b.end_date_obj;
                });
            } else {
                challengeList.sort(function (a, b) {
                    return a.start_date_obj - b.start_date_obj;
                });
            }
        }

        vm.resetFilters = function () {
            vm.filter = {
                organization: '',
                tags: '',
                sortByStartDate: false,
                sortByEndDate: false
            };
            
            // Reset filtered lists to original lists
            vm.filteredCurrentList = angular.copy(vm.currentList);
            vm.filteredUpcomingList = angular.copy(vm.upcomingList);
            vm.filteredPastList = angular.copy(vm.pastList);
            
            vm.hasAppliedFilter = false;

            if (!$scope.$$phase) {
                $scope.$apply();
            }
        };

        vm.hasAppliedFilter = false;

        vm.scrollUp = function () {
            angular.element($window).bind('scroll', function () {
                if (this.pageYOffset >= 100) {
                    utilities.showButton();
                } else {
                    utilities.hideButton();
                }
            });
        };

        function init() {
            vm.isFilterVisible = false;
        }

        init();

        // Bind controller functions to scope for access in view
        $scope.applyFilter = vm.applyFilter;
        $scope.resetFilters = vm.resetFilters;
        $scope.scrollUp = function () {
            $window.scrollTo(0, 0);
        };
        $scope.shortenDescription = function (desc) {
            return desc && desc.length > 100 ? desc.substring(0, 100) + '...' : desc;
        };

        $scope.isLoading = false;
        $scope.isNext = false;
        $scope.isPrev = false;
    }
})();