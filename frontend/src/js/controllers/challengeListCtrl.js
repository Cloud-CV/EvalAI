// Invoking IIFE for challenge page
(function() {

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

        vm.noneCurrentChallenge = false;
        vm.noneUpcomingChallenge = false;
        vm.nonePastChallenge = false;
        
        vm.pagination = {
            current: { page: 1, hasMore: false, loading: false, initialized: false },
            upcoming: { page: 1, hasMore: false, loading: false, initialized: false },
            past: { page: 1, hasMore: false, loading: false, initialized: false }
        };
        
        vm.itemsPerPage = 12; 
        vm.challengeCreator = {};
        vm.activeTab = 'current'; // Track which tab is currently active

        vm.getAllResults = function(parameters, challengeList, noneFlag, paginationType) {
            // Default to page 1 if paginationType is undefined
            if (!paginationType) {
                paginationType = parameters.url.includes('present') ? 'current' :
                                parameters.url.includes('future') ? 'upcoming' :
                                parameters.url.includes('past') ? 'past' : 'current';
            }
            
            if (!vm.pagination[paginationType]) {
                console.error("Invalid pagination type:", paginationType);
                utilities.hideLoader();
                return;
            }
            
            // If already loading, don't make another request
            if (vm.pagination[paginationType].loading) {
                return;
            }
            
            vm.pagination[paginationType].loading = true;
            
            var requestParams = angular.copy(parameters);
            
            requestParams.url = requestParams.url + '?page=' + vm.pagination[paginationType].page + '&page_size=' + vm.itemsPerPage;
            
            requestParams.callback = {
                onSuccess: function(response) {
                    var data = response.data;
                    
                    if (!data || !data.results || data.results.length === 0) {
                        if (vm.pagination[paginationType].page === 1) {
                            vm[noneFlag] = true;
                        }
                    } else {
                        if (vm.pagination[paginationType].page === 1) {
                            challengeList.length = 0;
                        }
                        
                        var timezone = moment.tz.guess();
                        for (var i = 0; i < data.results.length; i++) {
                            var result = data.results[i];
                            
                            if (result.description) {
                                var descLength = result.description.length;
                                result.isLarge = descLength >= 50 ? "..." : "";
                            } else {
                                result.description = "";
                                result.isLarge = "";
                            }
                            
                            if (result.start_date) {
                                var offset = new Date(result.start_date).getTimezoneOffset();
                                result.time_zone = moment.tz.zone(timezone).abbr(offset);
                                result.gmt_zone = gmtZone;
                            }
                            
                            if (result.id && result.creator && result.creator.id) {
                                var id = result.id;
                                vm.challengeCreator[id] = result.creator.id;
                                utilities.storeData("challengeCreator", vm.challengeCreator);
                            }
                        }
                        
                        Array.prototype.push.apply(challengeList, data.results);
                        vm.pagination[paginationType].hasMore = data.next !== null;
                    }
                    
                    vm.pagination[paginationType].loading = false;
                    vm.pagination[paginationType].initialized = true;
                    
                    if (paginationType === 'current') {
                        utilities.hideLoader();
                    }

                    if (!$scope.$$phase) {
                        $scope.$apply();
                    }
                },
                onError: function(error) {
                    console.error("API request failed:", error);
                    if (vm.pagination[paginationType].page === 1) {
                        vm[noneFlag] = true;
                    }
                    vm.pagination[paginationType].loading = false;
                    vm.pagination[paginationType].initialized = true;
                    
                    if (paginationType === 'current') {
                        utilities.hideLoader();
                    }

                    if (!$scope.$$phase) {
                        $scope.$apply();
                    }
                }
            };
        
            utilities.sendRequest(requestParams);
        };
        
        vm.loadMore = function(type) {
            if (vm.pagination[type].loading || !vm.pagination[type].hasMore) return;
            
            vm.pagination[type].page++;
            var parameters = {};
            if (userKey) {
                parameters.token = userKey;
            } else {
                parameters.token = null;
            }
            parameters.method = 'GET';
            
            switch(type) {
                case 'current':
                    parameters.url = 'challenges/challenge/present/approved/public';
                    vm.getAllResults(parameters, vm.currentList, "noneCurrentChallenge", "current");
                    break;
                case 'upcoming':
                    parameters.url = 'challenges/challenge/future/approved/public';
                    vm.getAllResults(parameters, vm.upcomingList, "noneUpcomingChallenge", "upcoming");
                    break;
                case 'past':
                    parameters.url = 'challenges/challenge/past/approved/public';
                    vm.getAllResults(parameters, vm.pastList, "nonePastChallenge", "past");
                    break;
            }
        };

        vm.imageLoaded = function(event) {
            event.target.classList.add('loaded');
        };
        
        // Function to initialize a specific tab's content
        vm.initializeTab = function(type) {
            if (vm.pagination[type].initialized) {
                return; // Already loaded
            }
            
            var parameters = {};
            if (userKey) {
                parameters.token = userKey;
            } else {
                parameters.token = null;
            }
            parameters.method = 'GET';
            
            switch(type) {
                case 'current':
                    parameters.url = 'challenges/challenge/present/approved/public';
                    vm.getAllResults(parameters, vm.currentList, "noneCurrentChallenge", "current");
                    break;
                case 'upcoming':
                    parameters.url = 'challenges/challenge/future/approved/public';
                    vm.getAllResults(parameters, vm.upcomingList, "noneUpcomingChallenge", "upcoming");
                    break;
                case 'past':
                    parameters.url = 'challenges/challenge/past/approved/public';
                    vm.getAllResults(parameters, vm.pastList, "nonePastChallenge", "past");
                    break;
            }
        };
        
        // Set active tab
        vm.setActiveTab = function(type) {
            vm.activeTab = type;
            vm.initializeTab(type);
        };
        
        vm.initScrollListener = function() {
            angular.element($window).bind('scroll', function() {
                // Show/hide scroll up button
                if (this.pageYOffset >= 100) {
                    utilities.showButton();
                } else {
                    utilities.hideButton();
                }
                
                var windowHeight = window.innerHeight;
                var scrollPosition = window.pageYOffset;
                var documentHeight = document.documentElement.scrollHeight;
                
                if (scrollPosition + windowHeight >= documentHeight - 500) {
                    var sections = document.querySelectorAll('.challenge-page-title');
                    var currentSection = '';
                    
                    for (var i = 0; i < sections.length; i++) {
                        var rect = sections[i].getBoundingClientRect();
                        if (rect.top > -100 && rect.top < windowHeight) {
                            currentSection = sections[i].textContent.trim().toLowerCase();
                            break;
                        }
                    }
                    
                    if (currentSection.indexOf('ongoing') !== -1) {
                        vm.initializeTab('current');
                        if (vm.pagination.current.hasMore) {
                            $scope.$apply(function() {
                                vm.loadMore('current');
                            });
                        }
                    } else if (currentSection.indexOf('upcoming') !== -1) {
                        vm.initializeTab('upcoming');
                        if (vm.pagination.upcoming.hasMore) {
                            $scope.$apply(function() {
                                vm.loadMore('upcoming');
                            });
                        }
                    } else if (currentSection.indexOf('past') !== -1) {
                        vm.initializeTab('past');
                        if (vm.pagination.past.hasMore) {
                            $scope.$apply(function() {
                                vm.loadMore('past');
                            });
                        }
                    }
                }
            });
        };
        
        // Initialize only current challenges on page load
        var currentParams = {};
        if (userKey) {
            currentParams.token = userKey;
        } else {
            currentParams.token = null;
        }
        currentParams.method = 'GET';
        currentParams.url = 'challenges/challenge/present/approved/public';
        vm.getAllResults(currentParams, vm.currentList, "noneCurrentChallenge", "current");
        
        // Add a method to detect when tabs are visible
        vm.checkVisibility = function() {
            var sections = document.querySelectorAll('.challenge-page-title');
            for (var i = 0; i < sections.length; i++) {
                var rect = sections[i].getBoundingClientRect();
                if (rect.top > -100 && rect.top < window.innerHeight) {
                    var sectionText = sections[i].textContent.trim().toLowerCase();
                    if (sectionText.indexOf('upcoming') !== -1) {
                        vm.initializeTab('upcoming');
                    } else if (sectionText.indexOf('past') !== -1) {
                        vm.initializeTab('past');
                    }
                }
            }
            
            // Check again after a delay
            $timeout(vm.checkVisibility, 1000);
        };

        vm.scrollUp = function() {
            $window.scrollTo(0, 0);
        };
        
        angular.element(document).ready(function() {
            vm.initScrollListener();
            
            // Start checking visibility of sections
            $timeout(vm.checkVisibility, 500);
            
            // Explicitly initialize past challenges after a short delay to ensure they load
            $timeout(function() {
                vm.initializeTab('past');
            }, 2000);
        });
    }
})();