// Invoking IIFE for challenge page
(function() {

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

        vm.currentList = [];
        vm.upcomingList = [];
        vm.pastList = [];

        vm.noneCurrentChallenge = false;
        vm.noneUpcomingChallenge = false;
        vm.nonePastChallenge = false;
        
        vm.pagination = {
            current: { page: 1, hasMore: false, loading: false },
            upcoming: { page: 1, hasMore: false, loading: false },
            past: { page: 1, hasMore: false, loading: false }
        };
        
        vm.itemsPerPage = 12; 
        vm.challengeCreator = {};

        vm.getAllResults = function(parameters, challengeList, noneFlag, paginationType) {
            if (!paginationType || !vm.pagination[paginationType]) {
                console.error("Invalid pagination type:", paginationType);
                utilities.hideLoader();
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
                        
                        challengeList.push.apply(challengeList, data.results);
                        vm.pagination[paginationType].hasMore = data.next !== null;
                    }
                    
                    vm.pagination[paginationType].loading = false;
                    utilities.hideLoader();
                },
                onError: function(error) {
                    console.error("API request failed:", error);
                    if (vm.pagination[paginationType].page === 1) {
                        vm[noneFlag] = true;
                    }
                    vm.pagination[paginationType].loading = false;
                    utilities.hideLoader(); 
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
                    
                    if (currentSection.indexOf('ongoing') !== -1 && vm.pagination.current.hasMore) {
                        $scope.$apply(function() {
                            vm.loadMore('current');
                        });
                    } else if (currentSection.indexOf('upcoming') !== -1 && vm.pagination.upcoming.hasMore) {
                        $scope.$apply(function() {
                            vm.loadMore('upcoming');
                        });
                    } else if (currentSection.indexOf('past') !== -1 && vm.pagination.past.hasMore) {
                        $scope.$apply(function() {
                            vm.loadMore('past');
                        });
                    }
                }
            });
        };
        
        // Initialize API calls
        var parameters = {};
        if (userKey) {
            parameters.token = userKey;
        } else {
            parameters.token = null;
        }
        parameters.method = 'GET';

        // Load current challenges
        var currentParams = angular.copy(parameters);
        currentParams.url = 'challenges/challenge/present/approved/public';
        vm.getAllResults(currentParams, vm.currentList, "noneCurrentChallenge", "current");
        
        // Load upcoming challenges
        var upcomingParams = angular.copy(parameters);
        upcomingParams.url = 'challenges/challenge/future/approved/public';
        vm.getAllResults(upcomingParams, vm.upcomingList, "noneUpcomingChallenge", "upcoming");

        // Load past challenges
        var pastParams = angular.copy(parameters);
        pastParams.url = 'challenges/challenge/past/approved/public';
        vm.getAllResults(pastParams, vm.pastList, "nonePastChallenge", "past");

        vm.scrollUp = function() {
            $window.scrollTo(0, 0);
        };
        
        angular.element(document).ready(function() {
            vm.initScrollListener();
        });
        
    }
})();