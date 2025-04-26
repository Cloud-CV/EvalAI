'use strict';

angular.module('evalai')
    .controller('ChallengeListCtrl', ['$timeout', 'utilities', function($timeout, utilities) {
        var vm = this;

        // Default variables
        vm.currentList = [];
        vm.filteredChallenges = [];
        vm.noneCurrentChallenge = false;
        vm.challengeCreator = {};
        vm.searchQuery = '';
        vm.isFilterVisible = false;
        vm.hasAppliedFilter = false;
        vm.filter = {
            organization: '',
            tags: '',
            sortByStartDate: false,
            sortByEndDate: false
        };

        // Show the loader
        utilities.showLoader();
        
        // Get user authentication status from the backend
        var userKey = utilities.getData('userKey');

        /**
         * Handle API errors
         * @param {Object} error - The error object
         * @param {String} message - Error message to display
         */
        function handleApiError(error, message = "Failed to load challenges. Please try again later.") {
            utilities.hideLoader();
            vm.errorMessage = message;
        }

        /**
         * Process challenge data and add additional properties
         * @param {Array} challenges - Array of challenge objects
         * @returns {Array} Processed challenges
         */
        function processChallenges(challenges) {
            challenges.forEach(function(challenge) {
                // Set isLarge property for description truncation
                challenge.isLarge = challenge.description && challenge.description.length >= 50 ? "..." : "";

                // Calculate timezone
                const timezone = moment.tz.guess();
                const zone = moment.tz.zone(timezone);
                const offset = new Date(challenge.start_date).getTimezoneOffset();
                challenge.time_zone = zone.abbr(offset);

                // Store creator info in challengeCreator object
                vm.challengeCreator[challenge.id] = challenge.creator.id;

                // Create Date objects for sorting purposes
                challenge.start_date_obj = new Date(challenge.start_date);
                challenge.end_date_obj = new Date(challenge.end_date);
            });

            // Store challengeCreator in localStorage
            utilities.storeData("challengeCreator", vm.challengeCreator);

            // Default sort by start date
            return challenges.sort((a, b) => a.start_date_obj - b.start_date_obj);
        }

        /**
         * Fetch all paginated results
         * @param {Object} parameters - API call parameters
         * @param {Array} results - Accumulated results
         * @param {String} noneFlag - Flag to set if no results
         */
        vm.getAllResults = function(parameters, results, noneFlag) {
            utilities.sendRequest(parameters).then(function(response) {
                const data = response.data;
                Array.prototype.push.apply(results, data.results);

                if (data.next) {
                    // If there's a next page, recursively fetch it
                    parameters.url = data.next.split('/api/')[1];
                    vm.getAllResults(parameters, results, noneFlag);
                } else {
                    // Process final results
                    if (results.length === 0) {
                        vm[noneFlag] = true;
                    } else {
                        results = processChallenges(results);
                    }

                    utilities.hideLoader();
                    $timeout.flush(); // Ensure $timeout is properly flushed
                }
            }).catch(function(error) {
                handleApiError(error);
            });
        };

        /**
         * Fetch present challenges
         */
        function getPresentChallenges() {
            const parameters = {
                url: 'challenges/challenge/present/approved/public',
                method: 'GET',
                callback: {
                    onSuccess: function(response) {
                        const data = response.data;

                        if (data.results.length === 0) {
                            vm.noneCurrentChallenge = true;
                        } else {
                            vm.currentList = processChallenges(data.results);
                        }

                        if (data.next) {
                            parameters.url = data.next.split('/api/')[1];
                            vm.getAllResults(parameters, vm.currentList, 'noneCurrentChallenge');
                        } else {
                            utilities.hideLoader();
                        }
                    },
                    onError: function(response) {
                        handleApiError(response.data);
                    }
                }
            };
            
            utilities.sendRequest(parameters);
        }

        /**
         * Toggle filter panel visibility
         */
        vm.toggleFilterPanel = function() {
            vm.isFilterVisible = !vm.isFilterVisible;
        };

        /**
         * Reset all filters
         */
        vm.resetFilters = function() {
            vm.filter = {
                organization: '',
                tags: '',
                sortByStartDate: false,
                sortByEndDate: false
            };
            vm.filteredChallenges = [];
            vm.hasAppliedFilter = false;
        };

        /**
         * Apply filters to challenge list
         */
        vm.applyFilter = function() {
            vm.hasAppliedFilter = true;
            let filteredResults = vm.currentList.slice();

            // Filter by organization
            if (vm.filter.organization) {
                filteredResults = filteredResults.filter(challenge =>
                    challenge.creator.team_name.toLowerCase().includes(vm.filter.organization.toLowerCase())
                );
            }

            // Filter by tags
            if (vm.filter.tags) {
                const tagArray = vm.filter.tags.toLowerCase().split(',').map(tag => tag.trim());

                filteredResults = filteredResults.filter(challenge => {
                    return challenge.list_tags && challenge.list_tags.some(tag =>
                        tagArray.some(t => tag.toLowerCase().includes(t))
                    );
                });
            }

            // Apply sorting
            if (vm.filter.sortByEndDate) {
                filteredResults.sort((a, b) => a.end_date_obj - b.end_date_obj);
            } else if (vm.filter.sortByStartDate) {
                filteredResults.sort((a, b) => a.start_date_obj - b.start_date_obj);
            }

            vm.filteredChallenges = filteredResults;
        };

        /**
         * Setup scroll event handling
         */
        vm.scrollUp = function() {
            angular.element(window).bind('scroll', function() {
                if (this.pageYOffset >= 100) {
                    utilities.showButton();
                } else {
                    utilities.hideButton();
                }
            });
        };

        // Initialize controller
        getPresentChallenges();
        vm.scrollUp();

        return vm;
    }]);
