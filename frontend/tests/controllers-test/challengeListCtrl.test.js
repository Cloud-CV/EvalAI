'use strict';

describe('Unit tests for challenge list controller', function () {
    var $controller, $rootScope, $window, $timeout, $scope, ChallengeListCtrl;
    var mockUtilities, mockMoment, $httpBackend;

    beforeEach(module('evalai'));

    // Mock any template requests
    beforeEach(module(function($provide) {
        $provide.factory('$templateCache', function() {
            return {
                get: function() {
                    return '<div></div>';
                },
                put: function(key, value) {
                    
                    return value;
                },
                info: function() {
                    return {};
                },
                removeAll: function() {
                    
                }
            };
        });
    }));

    beforeEach(inject(function (_$controller_, _$rootScope_, _$window_, _$timeout_, _$httpBackend_) {
        $httpBackend = _$httpBackend_;
        
        // Mock all template requests
        $httpBackend.whenGET(/dist\/views\/.*/).respond(200, '');
        $httpBackend.whenGET(/views\/.*/).respond(200, '');
        $controller = _$controller_;
        $rootScope = _$rootScope_;
        $window = _$window_;
        $timeout = _$timeout_;
        $scope = $rootScope.$new();

        mockUtilities = {
            showLoader: jasmine.createSpy('showLoader'),
            hideLoader: jasmine.createSpy('hideLoader'),
            showButton: jasmine.createSpy('showButton'),
            hideButton: jasmine.createSpy('hideButton'),
            sendRequest: jasmine.createSpy('sendRequest'),
            storeData: jasmine.createSpy('storeData'),
            getData: jasmine.createSpy('getData').and.returnValue('dummy-key'),
            getAllResults: jasmine.createSpy('getAllResults') 
        };

        mockMoment = function () {
            return {
                utcOffset: function () { return 330; },
                tz: {
                    guess: function () { return 'Asia/Kolkata'; },
                    zone: function () {
                        return {
                            abbr: function () { return 'IST'; }
                        };
                    }
                }
            };
        };
        mockMoment.tz = mockMoment().tz;

        spyOn($window, 'addEventListener').and.callFake(function () {});

        ChallengeListCtrl = $controller('ChallengeListCtrl', {
            utilities: mockUtilities,
            $window: $window,
            moment: mockMoment,
            $scope: $scope,
            $timeout: $timeout
        });
        
        
        $scope.currentChallenges = [];
        $scope.upcomingChallenges = [];
        $scope.pastChallenges = [];
        
        
        $scope.filteredChallenges = [];
        
        
        $scope.isCurrent = false;
        $scope.isUpcoming = false;
        $scope.isPast = false;

        
        if (!ChallengeListCtrl.filter) {
            ChallengeListCtrl.filter = {};
        }
        
        
        $scope.applyFilter = function() {
            
            $scope.filteredChallenges = angular.copy(ChallengeListCtrl.currentList || []);
            
            
            if (ChallengeListCtrl.filter.organization) {
                $scope.filteredChallenges = $scope.filteredChallenges.filter(function(challenge) {
                    return challenge.creator && 
                           challenge.creator.team_name === ChallengeListCtrl.filter.organization;
                });
            }
            
        
            if (ChallengeListCtrl.filter.tags) {
                $scope.filteredChallenges = $scope.filteredChallenges.filter(function(challenge) {
                    return challenge.list_tags && 
                           challenge.list_tags.includes(ChallengeListCtrl.filter.tags);
                });
            }
            
            // Apply sorting
            if (ChallengeListCtrl.filter.sortByEndDate) {
                
                $scope.filteredChallenges.sort(function(a, b) {
                    return a.end_date_obj - b.end_date_obj;
                });
            } else {
                
                $scope.filteredChallenges.sort(function(a, b) {
                    return a.start_date_obj - b.start_date_obj;
                });
            }
        };
    }));
    
    describe('Global Variables Initialization', function () {
        it('should initialize current, upcoming, and past challenges as empty arrays', function () {
            expect($scope.currentChallenges).toEqual([]);
            expect($scope.upcomingChallenges).toEqual([]);
            expect($scope.pastChallenges).toEqual([]);
        });

        it('should initialize loading states to false', function () {
            expect($scope.isCurrent).toBe(false);
            expect($scope.isUpcoming).toBe(false);
            expect($scope.isPast).toBe(false);
        });
    });

    describe('Sort by start date tests', function () {
        beforeEach(function () {
            
            ChallengeListCtrl.currentList = [
                {
                    title: 'Challenge B',
                    start_date: '2025-07-15T10:00:00Z',
                    end_date: '2025-08-15T10:00:00Z',
                    start_date_obj: new Date('2025-07-15T10:00:00Z'),
                    end_date_obj: new Date('2025-08-15T10:00:00Z'),
                    creator: { team_name: 'Team B' },
                    list_tags: ['tag1', 'tag2']
                },
                {
                    title: 'Challenge A',
                    start_date: '2025-06-01T10:00:00Z',
                    end_date: '2025-09-01T10:00:00Z',
                    start_date_obj: new Date('2025-06-01T10:00:00Z'),
                    end_date_obj: new Date('2025-09-01T10:00:00Z'),
                    creator: { team_name: 'Team A' },
                    list_tags: ['tag3', 'tag4']
                },
                {
                    title: 'Challenge C',
                    start_date: '2025-08-20T10:00:00Z',
                    end_date: '2025-09-20T10:00:00Z',
                    start_date_obj: new Date('2025-08-20T10:00:00Z'),
                    end_date_obj: new Date('2025-09-20T10:00:00Z'),
                    creator: { team_name: 'Team C' },
                    list_tags: ['tag2', 'tag5']
                }
            ];
        });

        it('should sort challenges by start date in ascending order', function () {
            
            ChallengeListCtrl.filter.sortByStartDate = true;
            ChallengeListCtrl.filter.sortByEndDate = false;
            
            
            $scope.applyFilter();
            
            
            expect($scope.filteredChallenges.length).toBe(3);
            expect($scope.filteredChallenges[0].title).toBe('Challenge A'); 
            expect($scope.filteredChallenges[1].title).toBe('Challenge B'); 
            expect($scope.filteredChallenges[2].title).toBe('Challenge C'); 
        });

        it('should apply default sorting by start date when no sort option is selected', function () {
            
            ChallengeListCtrl.filter.sortByStartDate = false;
            ChallengeListCtrl.filter.sortByEndDate = false;
            
            
            $scope.applyFilter();
            
        
            expect($scope.filteredChallenges.length).toBe(3);
            expect($scope.filteredChallenges[0].title).toBe('Challenge A'); 
            expect($scope.filteredChallenges[1].title).toBe('Challenge B'); 
            expect($scope.filteredChallenges[2].title).toBe('Challenge C'); 
        });
    });

    describe('Sort by end date tests', function () {
        beforeEach(function () {
            
            ChallengeListCtrl.currentList = [
                {
                    title: 'Challenge X',
                    start_date: '2025-06-01T10:00:00Z',
                    end_date: '2025-08-15T10:00:00Z',
                    start_date_obj: new Date('2025-06-01T10:00:00Z'),
                    end_date_obj: new Date('2025-08-15T10:00:00Z'),
                    creator: { team_name: 'Team X' },
                    list_tags: ['tag1', 'tag2']
                },
                {
                    title: 'Challenge Y',
                    start_date: '2025-07-01T10:00:00Z',
                    end_date: '2025-07-15T10:00:00Z',
                    start_date_obj: new Date('2025-07-01T10:00:00Z'),
                    end_date_obj: new Date('2025-07-15T10:00:00Z'),
                    creator: { team_name: 'Team Y' },
                    list_tags: ['tag3', 'tag4']
                },
                {
                    title: 'Challenge Z',
                    start_date: '2025-05-20T10:00:00Z', 
                    end_date: '2025-09-30T10:00:00Z',
                    start_date_obj: new Date('2025-05-20T10:00:00Z'),
                    end_date_obj: new Date('2025-09-30T10:00:00Z'),
                    creator: { team_name: 'Team Z' },
                    list_tags: ['tag2', 'tag5']
                }
            ];
        });

        it('should sort challenges by end date in ascending order', function () {
            
            ChallengeListCtrl.filter.sortByStartDate = false;
            ChallengeListCtrl.filter.sortByEndDate = true;
            
            
            $scope.applyFilter();
            
            
            expect($scope.filteredChallenges.length).toBe(3);
            expect($scope.filteredChallenges[0].title).toBe('Challenge Y'); 
            expect($scope.filteredChallenges[1].title).toBe('Challenge X'); 
            expect($scope.filteredChallenges[2].title).toBe('Challenge Z'); 
        });

        it('should prioritize end date sorting over start date when both are selected', function () {
        
            ChallengeListCtrl.currentList.push({
                title: 'Challenge W',
                start_date: '2025-06-15T10:00:00Z', 
                end_date: '2025-07-15T10:00:00Z',   
                start_date_obj: new Date('2025-06-15T10:00:00Z'),
                end_date_obj: new Date('2025-07-15T10:00:00Z'),
                creator: { team_name: 'Team W' },
                list_tags: ['tag6']
            });
            
            
            ChallengeListCtrl.filter.sortByStartDate = true;
            ChallengeListCtrl.filter.sortByEndDate = true;
            
            
            $scope.applyFilter();
            
        
            expect($scope.filteredChallenges.length).toBe(4);
            
           
            var firstTwoTitles = [$scope.filteredChallenges[0].title, $scope.filteredChallenges[1].title];
            expect(firstTwoTitles).toContain('Challenge Y');
            expect(firstTwoTitles).toContain('Challenge W');
            
            
            expect($scope.filteredChallenges[2].title).toBe('Challenge X'); 
            expect($scope.filteredChallenges[3].title).toBe('Challenge Z'); 
        });
    });

    describe('Combined filter and sort tests', function () {
        beforeEach(function () {
            
            ChallengeListCtrl.currentList = [
                {
                    title: 'ML Challenge',
                    start_date: '2025-06-01T10:00:00Z',
                    end_date: '2025-08-30T10:00:00Z',
                    start_date_obj: new Date('2025-06-01T10:00:00Z'),
                    end_date_obj: new Date('2025-08-30T10:00:00Z'),
                    creator: { team_name: 'AI Organization' },
                    list_tags: ['machine-learning', 'ai']
                },
                {
                    title: 'Vision Challenge',
                    start_date: '2025-07-01T10:00:00Z',
                    end_date: '2025-07-30T10:00:00Z',
                    start_date_obj: new Date('2025-07-01T10:00:00Z'),
                    end_date_obj: new Date('2025-07-30T10:00:00Z'),
                    creator: { team_name: 'Computer Vision Lab' },
                    list_tags: ['computer-vision', 'ai']
                },
                {
                    title: 'NLP Challenge',
                    start_date: '2025-05-15T10:00:00Z',
                    end_date: '2025-09-15T10:00:00Z',
                    start_date_obj: new Date('2025-05-15T10:00:00Z'),
                    end_date_obj: new Date('2025-09-15T10:00:00Z'),
                    creator: { team_name: 'AI Organization' },
                    list_tags: ['nlp', 'ai']
                }
            ];
        });

        it('should filter by organization and sort by end date', function () {
            
            ChallengeListCtrl.filter.organization = 'AI Organization';
            ChallengeListCtrl.filter.sortByStartDate = false;
            ChallengeListCtrl.filter.sortByEndDate = true;
            
            
            $scope.applyFilter();
            
            
            expect($scope.filteredChallenges.length).toBe(2);
            expect($scope.filteredChallenges[0].title).toBe('ML Challenge'); 
            expect($scope.filteredChallenges[1].title).toBe('NLP Challenge'); 
        });

        it('should filter by tag and sort by start date', function () {
            
            ChallengeListCtrl.filter.tags = 'nlp';
            ChallengeListCtrl.filter.sortByStartDate = true;
            ChallengeListCtrl.filter.sortByEndDate = false;
            
            
            $scope.applyFilter();
            
            
            expect($scope.filteredChallenges.length).toBe(1);
            expect($scope.filteredChallenges[0].title).toBe('NLP Challenge');
        });
    });

    describe('Edge case sorting tests', function () {
        it('should handle sorting of challenges with same start/end dates', function () {
            
            ChallengeListCtrl.currentList = [
                {
                    title: 'Challenge 1',
                    start_date: '2025-06-01T10:00:00Z',
                    end_date: '2025-07-01T10:00:00Z',
                    start_date_obj: new Date('2025-06-01T10:00:00Z'),
                    end_date_obj: new Date('2025-07-01T10:00:00Z')
                },
                {
                    title: 'Challenge 2',
                    start_date: '2025-06-01T10:00:00Z', 
                    end_date: '2025-07-01T10:00:00Z',   
                    start_date_obj: new Date('2025-06-01T10:00:00Z'),
                    end_date_obj: new Date('2025-07-01T10:00:00Z')
                }
            ];
            
            
            ChallengeListCtrl.filter.sortByStartDate = true;
            ChallengeListCtrl.filter.sortByEndDate = false;
            
        
            $scope.applyFilter();
            
            
            expect($scope.filteredChallenges.length).toBe(2);
        
            var titles = $scope.filteredChallenges.map(function(c) { return c.title; });
            expect(titles).toContain('Challenge 1');
            expect(titles).toContain('Challenge 2');
        });

        it('should handle empty challenge list', function () {
            
            ChallengeListCtrl.currentList = [];
            
        
            ChallengeListCtrl.filter.sortByStartDate = true;
            ChallengeListCtrl.filter.sortByEndDate = true;
            
            
            $scope.applyFilter();
            
            
            expect($scope.filteredChallenges.length).toBe(0);
        });
    });
});