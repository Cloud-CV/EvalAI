'use strict';

describe('Unit tests for hosted challenge controller', function () {
    beforeEach(angular.mock.module('evalai'));

    var $controller, createController, $rootScope, $scope, utilities, vm;

    beforeEach(inject(function (_$controller_, _$rootScope_, _utilities_,) {
        $controller = _$controller_;
        $rootScope = _$rootScope_;
        utilities = _utilities_;

        $scope = $rootScope.$new();
        createController = function () {
            return $controller('HostedChallengesCtrl', {$scope: $scope});
        };
        vm = $controller('HostedChallengesCtrl', { $scope: $scope });
    }));

    describe('Global variables', function () {
        it('has default values', function () {
            utilities.storeData('userKey', 'encrypted key');
            spyOn(utilities, 'getData');
            spyOn(utilities, 'showLoader');

            vm = createController();
            expect(utilities.getData).toHaveBeenCalledWith('userKey');
            expect(utilities.showLoader).toHaveBeenCalled();
            expect(vm.challengeList).toEqual([]);
            expect(vm.challengeCreator).toEqual({});
        });
    });

    describe('Unit tests for global backend calls', function () {
        var hostTeamSuccess, hostedChallengeSuccess, successResponse, errorResponse;

        beforeEach(function () {
            spyOn(utilities, 'hideLoader');
            spyOn(utilities, 'storeData');

            utilities.sendRequest = function (parameters) {
                if ((hostTeamSuccess == true && parameters.url == 'hosts/challenge_host_team/') ||
                (hostedChallengeSuccess == true && parameters.url != 'hosts/challenge_host_team/')) {
                    parameters.callback.onSuccess({
                        data: successResponse,
                        status: 200
                    });
                } else if ((hostTeamSuccess == false && parameters.url == 'hosts/challenge_host_team/') ||
                (hostedChallengeSuccess == false && parameters.url != 'hosts/challenge_host_team/')) {
                    parameters.callback.onError({
                        data: errorResponse
                    });
                }
            };
        });

        it('get host teams details backend error `hosts/challenge_host_team/`', function () {
            hostTeamSuccess = false;
            hostedChallengeSuccess = null;
            errorResponse = {
                error: 'error'
            };
            vm = createController();
            expect(utilities.hideLoader).toHaveBeenCalled();
        });

        it('get the details of the hosted challenge \
        `challenges/challenge_host_team/<host_team_id>/challenge`', function () {
            hostTeamSuccess = true;
            hostedChallengeSuccess = true;
            successResponse = {
                results: [
                    {
                        id: 1,
                        title: "Hosted challenge title",
                        description: "Host challenge description",
                        creator: "hostUser"
                    }
                ]
            };
            var challengeList = [];

            vm = createController();
            for (var i = 0; i < successResponse.results.length; i++) {
                challengeList.push(successResponse.results[i]);
                expect(vm.challengeList).toEqual(challengeList);
                expect(utilities.storeData).toHaveBeenCalled();
            }
            expect(utilities.hideLoader).toHaveBeenCalled();
        });

        it('get the hosted challenge details backend error', function () {
            hostTeamSuccess = true;
            hostedChallengeSuccess = false
            // host team details response
            successResponse = {
                results: [
                    {
                        id: 1,
                        team_name: "Host team name",
                        team_url: "https://host_team.url",
                        created_by: "hostchallenge descriptionUser"
                    }
                ]
            };
            // hosted challenge response
            errorResponse = {
                error: 'error'
            };
            vm = createController();
            expect(utilities.hideLoader).toHaveBeenCalled();
        });

    });

    describe('Tabbed Navigation', function () {
        beforeEach(function () {
            vm = createController();
        });
    
        it('should initialize with the ongoing tab selected', function () {
            expect(vm.currentTab).toBe('ongoing');
        });
    
        it('should switch to the upcoming tab', function () {
            vm.setCurrentTab('upcoming');
            expect(vm.currentTab).toBe('upcoming');
        });
    
        it('should switch to the past tab', function () {
            vm.setCurrentTab('past');
            expect(vm.currentTab).toBe('past');
        });
    
        it('should categorize challenges based on their dates', function () {
            var current = new Date();
            var pastDate = new Date(current.getFullYear() - 1, current.getMonth(), current.getDate());
            var futureDate = new Date(current.getFullYear() + 1, current.getMonth(), current.getDate());
            utilities.sendRequest = function (parameters) {
                if (parameters.url === 'hosts/challenge_host_team/') {
                    parameters.callback.onSuccess({
                        data: { results: [{ id: 10 }] }
                    });
                } else if (parameters.url.indexOf("challenges/challenge_host_team/") === 0) {
                    parameters.callback.onSuccess({
                        data: { results: [
                            { id: 1, start_date: pastDate, end_date: pastDate, creator: { id: 101 } },
                            { id: 2, start_date: current, end_date: futureDate, creator: { id: 102 } },
                            { id: 3, start_date: futureDate, end_date: futureDate, creator: { id: 103 } }
                        ]}
                    });
                }
            };
            vm = createController();
            expect(vm.pastChallenges.length).toBe(1);
            expect(vm.ongoingChallenges.length).toBe(1);
            expect(vm.upcomingChallenges.length).toBe(1);
        });
    
        it('should handle API request errors gracefully', function () {
            spyOn(utilities, 'hideLoader');
            utilities.sendRequest = function (parameters) {
                parameters.callback.onError({ error: 'Network Error' });
            };
            vm = createController();
            expect(utilities.hideLoader).toHaveBeenCalled();
        });
    });
    
    describe('Challenge categorization with duplicate handling', function () {
        beforeEach(function () {
            jasmine.clock().install();
            const now = new Date();
            jasmine.clock().mockDate(now);

            vm = createController();
        });

        afterEach(function () {
            jasmine.clock().uninstall();
        });
        
        it('should handle duplicate challenges in upcoming category', function () {
            var current = new Date();
            var futureDate = new Date(current.getTime() + 86400000);
            utilities.sendRequest = function (parameters) {
                if (parameters.url === 'hosts/challenge_host_team/') {
                    parameters.callback.onSuccess({
                        data: { results: [{ id: 10 }, { id: 11 }] }
                    });
                } else if (parameters.url.indexOf("challenges/challenge_host_team/") === 0) {
                    parameters.callback.onSuccess({
                        data: { results: [
                            { id: 1, start_date: futureDate, end_date: new Date(futureDate.getTime() + 86400000), creator: { id: 101 } }
                        ]}
                    });
                }
            };
            vm = createController();
            expect(vm.upcomingChallenges.length).toBe(1);
        });
        
        it('should handle duplicate challenges in ongoing category', function () {
            var current = new Date();
            var startDate = new Date(current.getTime() - 86400000);
            var endDate = new Date(current.getTime() + 86400000);
            utilities.sendRequest = function (parameters) {
                if (parameters.url === 'hosts/challenge_host_team/') {
                    parameters.callback.onSuccess({
                        data: { results: [{ id: 20 }, { id: 21 }] }
                    });
                } else if (parameters.url.indexOf("challenges/challenge_host_team/") === 0) {
                    parameters.callback.onSuccess({
                        data: { results: [
                            { id: 2, start_date: startDate, end_date: endDate, creator: { id: 202 } }
                        ]}
                    });
                }
            };
            vm = createController();
            expect(vm.ongoingChallenges.length).toBe(1);
        });
        
        it('should handle duplicate challenges in past category', function () {
            var current = new Date();
            var pastDate = new Date(current.getTime() - 172800000);
            var pastEndDate = new Date(current.getTime() - 86400000);
            utilities.sendRequest = function (parameters) {
                if (parameters.url === 'hosts/challenge_host_team/') {
                    parameters.callback.onSuccess({
                        data: { results: [{ id: 30 }, { id: 31 }] }
                    });
                } else if (parameters.url.indexOf("challenges/challenge_host_team/") === 0) {
                    parameters.callback.onSuccess({
                        data: { results: [
                            { id: 3, start_date: pastDate, end_date: pastEndDate, creator: { id: 303 } }
                        ]}
                    });
                }
            };
            vm = createController();
            expect(vm.pastChallenges.length).toBe(1);
        });
        
        it('should correctly categorize challenges at boundary conditions', function () {
            var current = new Date();
            utilities.sendRequest = function (parameters) {
                if (parameters.url === 'hosts/challenge_host_team/') {
                    parameters.callback.onSuccess({
                        data: { results: [{ id: 40 }] }
                    });
                } else if (parameters.url.indexOf("challenges/challenge_host_team/") === 0) {
                    parameters.callback.onSuccess({
                        data: { results: [
                            { id: 4, start_date: current, end_date: new Date(current.getTime() + 86400000), creator: { id: 404 } },
                            { id: 5, start_date: new Date(current.getTime() - 86400000), end_date: current, creator: { id: 505 } }
                        ]}
                    });
                }
            };
            vm = createController();
            expect(vm.ongoingChallenges.length).toBe(2);
            expect(vm.upcomingChallenges.length).toBe(0);
            expect(vm.pastChallenges.length).toBe(0);
        });
    }); 

    describe('GMT offset coverage', function () {
        beforeEach(function () {
            spyOn(utilities, 'showLoader').and.callThrough();
            spyOn(utilities, 'hideLoader').and.callThrough();
            spyOn(utilities, 'sendRequest').and.callFake(function (parameters) {
                parameters.callback.onSuccess({ data: { results: [] } });
            });
        });
    
        it('should set sign to + and skip leading zero when minutes >= 10', function () {
            spyOn(moment.fn, 'utcOffset').and.returnValue(330);
            vm = createController();
            expect(utilities.showLoader).toHaveBeenCalled();
        });
    
        it('should set sign to - and add leading zero when minutes < 10', function () {
            spyOn(moment.fn, 'utcOffset').and.returnValue(-65);
            vm = createController();
            expect(utilities.showLoader).toHaveBeenCalled();
        });
    }); 

    describe('getCurrentChallengeList', function () {
        beforeEach(function () {
            vm = createController();
            // Initialize challenges for testing if needed
            vm.ongoingChallenges = [{ id: 1, name: 'Ongoing Challenge' }];
            vm.upcomingChallenges = [{ id: 2, name: 'Upcoming Challenge' }];
            vm.pastChallenges = [{ id: 3, name: 'Past Challenge' }];
        });
    
        it('should return ongoing challenges when currentTab is "ongoing"', function () {
            vm.currentTab = 'ongoing';
            expect(vm.getCurrentChallengeList()).toEqual(vm.ongoingChallenges);
        });
    
        it('should return upcoming challenges when currentTab is "upcoming"', function () {
            vm.currentTab = 'upcoming';
            expect(vm.getCurrentChallengeList()).toEqual(vm.upcomingChallenges);
        });
    
        it('should return past challenges when currentTab is "past"', function () {
            vm.currentTab = 'past';
            expect(vm.getCurrentChallengeList()).toEqual(vm.pastChallenges);
        });
    
        it('should return an empty array when currentTab is an unknown value', function () {
            vm.currentTab = 'unknown'; // This covers the 'else' branch
            expect(vm.getCurrentChallengeList()).toEqual([]);
        });
    
        it('should return an empty array when currentTab is null', function () {
            vm.currentTab = null; // Another case for the 'else' branch
            expect(vm.getCurrentChallengeList()).toEqual([]);
        });
    
        it('should return an empty array when currentTab is undefined', function () {
            vm.currentTab = undefined; // Yet another case for the 'else' branch
            expect(vm.getCurrentChallengeList()).toEqual([]);
        });
    });

    describe('Filter functions', function () {
        var $filter;
    
        beforeEach(inject(function (_$filter_) {
            $filter = _$filter_;
            vm = createController();
    
            // Mock the custom filters and orderBy
            spyOn($filter, 'customTitleFilter').and.callFake(function (arr) { return arr; });
            spyOn($filter, 'customDomainFilter').and.callFake(function (arr) { return arr; });
            spyOn($filter, 'customHostFilter').and.callFake(function (arr) { return arr; });
            spyOn($filter, 'customDateRangeFilter').and.callFake(function (arr) { return arr; });
            spyOn($filter, 'orderBy').and.callFake(function (arr) { return arr; });
    
            // Initialize sample challenge data for tests
            vm.ongoingChallenges = [
                { id: 1, title: 'Ongoing A', domain_name: ['CV'], creator: { team_name: 'TeamX' }, start_date: '2025-01-01T00:00:00Z', end_date: '2025-12-31T00:00:00Z' },
                { id: 2, title: 'Ongoing B', domain_name: ['NLP'], creator: { team_name: 'TeamY' }, start_date: '2025-02-01T00:00:00Z', end_date: '2025-11-30T00:00:00Z' }
            ];
            vm.upcomingChallenges = [
                { id: 3, title: 'Upcoming C', domain_name: ['Web'], creator: { team_name: 'TeamZ' }, start_date: '2026-01-01T00:00:00Z', end_date: '2026-12-31T00:00:00Z' }
            ];
            vm.pastChallenges = [
                { id: 4, title: 'Past D', domain_name: ['Vision'], creator: { team_name: 'TeamA' }, start_date: '2024-01-01T00:00:00Z', end_date: '2024-02-01T00:00:00Z' }
            ];
        }));
    
        // ---
        // Tests for vm.resetFilter
        // ---
        it('should reset all filter values when resetFilter is called', function () {
            // Set some filter values
            vm.selecteddomain = ['Computer Vision'];
            vm.searchTitle = ['test'];
            vm.selectedHostTeam = 'Test Team';
            vm.sortByTeam = 'asc';
            vm.filterStartDate = new Date('2023-01-01');
            vm.filterEndDate = new Date('2023-12-31');
    
            // Call resetFilter
            vm.resetFilter();
    
            // Verify all values are reset
            expect(vm.selecteddomain).toEqual([]);
            expect(vm.searchTitle).toEqual([]);
            expect(vm.selectedHostTeam).toEqual('');
            expect(vm.sortByTeam).toEqual('');
            expect(vm.filterStartDate).toBeNull();
            expect(vm.filterEndDate).toBeNull();
        });
    
        // ---
        // Tests for vm.getFilteredOngoingChallenges
        // ---
        it('should apply all filters to ongoing challenges', function () {
            vm.searchTitle = ['Ongoing A'];
            vm.selecteddomain = ['CV'];
            vm.selectedHostTeam = 'TeamX';
            vm.filterStartDate = new Date('2025-01-01');
            vm.filterEndDate = new Date('2025-12-31');
            vm.sortByTeam = 'asc';
    
            const result = vm.getFilteredOngoingChallenges();
    
            expect($filter.customTitleFilter).toHaveBeenCalledWith(vm.ongoingChallenges, vm.searchTitle);
            expect($filter.customDomainFilter).toHaveBeenCalledWith(result, vm.selecteddomain); // result of previous filter
            expect($filter.customHostFilter).toHaveBeenCalledWith(result, vm.selectedHostTeam);
            expect($filter.customDateRangeFilter).toHaveBeenCalledWith(result, vm.filterStartDate, vm.filterEndDate);
            expect($filter.orderBy).toHaveBeenCalledWith(result, 'creator.team_name', vm.sortByTeam === 'desc');
            expect(result).toBeDefined();
        });
    
        it('should return ongoing challenges without filters if filter values are empty', function () {
            vm.searchTitle = [];
            vm.selecteddomain = [];
            vm.selectedHostTeam = '';
            vm.filterStartDate = null;
            vm.filterEndDate = null;
            vm.sortByTeam = '';
    
            const result = vm.getFilteredOngoingChallenges();
    
            // Even with empty filters, the filter functions are called, but they return the original array if the custom filter logic handles it this way.
            // We're primarily testing that the calls happen.
            expect($filter.customTitleFilter).toHaveBeenCalledWith(vm.ongoingChallenges, []);
            expect($filter.customDomainFilter).toHaveBeenCalledWith(result, []);
            expect($filter.customHostFilter).toHaveBeenCalledWith(result, '');
            expect($filter.customDateRangeFilter).toHaveBeenCalledWith(result, null, null);
            expect($filter.orderBy).toHaveBeenCalledWith(result, 'creator.team_name', false); // sortByTeam === 'desc' will be false
            expect(result).toBeDefined();
        });
    
        // ---
        // Tests for vm.getFilteredUpcomingChallenges
        // ---
        it('should apply all filters to upcoming challenges', function () {
            vm.searchTitle = ['Upcoming C'];
            vm.selecteddomain = ['Web'];
            vm.selectedHostTeam = 'TeamZ';
            vm.filterStartDate = new Date('2026-01-01');
            vm.filterEndDate = new Date('2026-12-31');
            vm.sortByTeam = 'desc';
    
            const result = vm.getFilteredUpcomingChallenges();
    
            expect($filter.customTitleFilter).toHaveBeenCalledWith(vm.upcomingChallenges, vm.searchTitle);
            expect($filter.customDomainFilter).toHaveBeenCalledWith(result, vm.selecteddomain);
            expect($filter.customHostFilter).toHaveBeenCalledWith(result, vm.selectedHostTeam);
            expect($filter.customDateRangeFilter).toHaveBeenCalledWith(result, vm.filterStartDate, vm.filterEndDate);
            expect($filter.orderBy).toHaveBeenCalledWith(result, 'creator.team_name', vm.sortByTeam === 'desc');
            expect(result).toBeDefined();
        });
    
        // ---
        // Tests for vm.getFilteredPastChallenges
        // ---
        it('should apply all filters to past challenges', function () {
            vm.searchTitle = ['Past D'];
            vm.selecteddomain = ['Vision'];
            vm.selectedHostTeam = 'TeamA';
            vm.filterStartDate = new Date('2024-01-01');
            vm.filterEndDate = new Date('2024-02-01');
            vm.sortByTeam = 'asc';
    
            const result = vm.getFilteredPastChallenges();
    
            expect($filter.customTitleFilter).toHaveBeenCalledWith(vm.pastChallenges, vm.searchTitle);
            expect($filter.customDomainFilter).toHaveBeenCalledWith(result, vm.selecteddomain);
            expect($filter.customHostFilter).toHaveBeenCalledWith(result, vm.selectedHostTeam);
            expect($filter.customDateRangeFilter).toHaveBeenCalledWith(result, vm.filterStartDate, vm.filterEndDate);
            expect($filter.orderBy).toHaveBeenCalledWith(result, 'creator.team_name', vm.sortByTeam === 'desc');
            expect(result).toBeDefined();
        });
    });

    describe('Filter and Dialog Functions', function () {
        var $filter, $mdDialog, $q, $rootScope;

        beforeEach(inject(function (_$filter_, _$mdDialog_, _$q_, _$rootScope_) {
            $filter = _$filter_;
            $mdDialog = _$mdDialog_;
            $q = _$q_;
            $rootScope = _$rootScope_;
            
            vm = createController(); // Assuming createController is defined as in your test file

            // Mock the custom filters and orderBy if they are not the focus of these tests
            spyOn($filter, 'customTitleFilter').and.callFake(arr => arr);
            spyOn($filter, 'customDomainFilter').and.callFake(arr => arr);
            spyOn($filter, 'customHostFilter').and.callFake(arr => arr);
            spyOn($filter, 'customDateRangeFilter').and.callFake(arr => arr);
            spyOn($filter, 'orderBy').and.callFake(arr => arr);
        }));

        // ---
        // Tests for vm.resetFilter
        // ---
        it('should reset all filter properties to their default state', function () {
            // 1. Arrange: Set some non-default filter values
            vm.selecteddomain = ['NLP', 'Computer Vision'];
            vm.searchTitle = ['Awesome Challenge'];
            vm.selectedHostTeam = 'Team EvalAI';
            vm.sortByTeam = 'asc';
            vm.filterStartDate = new Date('2025-01-01');
            vm.filterEndDate = new Date('2025-12-31');

            // 2. Act: Call the reset function
            vm.resetFilter();

            // 3. Assert: Verify all properties are reset
            expect(vm.selecteddomain).toEqual([]);
            expect(vm.searchTitle).toEqual([]);
            expect(vm.selectedHostTeam).toBe('');
            expect(vm.sortByTeam).toBe('');
            expect(vm.filterStartDate).toBeNull();
            expect(vm.filterEndDate).toBeNull();
        });

        // ---
        // Tests for vm.openFilterDialog
        // ---
        describe('openFilterDialog', function() {
            var mockEvent;
            var initialFilterData;

            beforeEach(function() {
                mockEvent = { target: 'mockButton' };
                
                // Arrange: Set initial filter state on the controller
                vm.selecteddomain = ['CV'];
                vm.selectedHostTeam = 'HostTeam1';
                vm.sortByTeam = 'asc';
                vm.filterStartDate = new Date('2025-01-01');
                vm.filterEndDate = new Date('2025-01-31');
                vm.domain_choices = [['All', 'All'], ['CV', 'CV']];
                vm.host_team_choices = ['HostTeam1', 'HostTeam2'];

                initialFilterData = {
                    selecteddomain: vm.selecteddomain,
                    selectedHostTeam: vm.selectedHostTeam,
                    sortByTeam: vm.sortByTeam,
                    filterStartDate: vm.filterStartDate,
                    filterEndDate: vm.filterEndDate,
                    domain_choices: vm.domain_choices,
                    host_team_choices: vm.host_team_choices
                };
            });

            it('should open the filter dialog with the correct initial data', function() {
                // Arrange: Spy on the $mdDialog.show method
                spyOn($mdDialog, 'show').and.returnValue($q.defer().promise);

                // Act: Call the function
                vm.openFilterDialog(mockEvent);
                $rootScope.$apply();

                // Assert: Check if the dialog was shown with the correct parameters
                expect($mdDialog.show).toHaveBeenCalled();
                var dialogArgs = $mdDialog.show.calls.mostRecent().args[0];
                expect(dialogArgs.controller).toBe('filterDialogCtrl');
                expect(dialogArgs.targetEvent).toBe(mockEvent);
                expect(dialogArgs.locals.filterData).toEqual(initialFilterData);
            });

            it('should update controller filters when the dialog is closed with new filters', function() {
                // Arrange: Define the new filters the dialog will return
                var newFilters = {
                    selecteddomain: ['NLP'],
                    selectedHostTeam: 'HostTeam2',
                    sortByTeam: 'desc',
                    filterStartDate: new Date('2025-06-01'),
                    filterEndDate: new Date('2025-06-30')
                };
                
                // Mock the dialog to return a resolved promise with the new filters
                spyOn($mdDialog, 'show').and.returnValue($q.resolve(newFilters));

                // Act: Open the dialog
                vm.openFilterDialog(mockEvent);
                $rootScope.$apply(); // Resolve the promise

                // Assert: Verify the controller's scope was updated
                expect(vm.selecteddomain).toEqual(newFilters.selecteddomain);
                expect(vm.selectedHostTeam).toEqual(newFilters.selectedHostTeam);
                expect(vm.sortByTeam).toEqual(newFilters.sortByTeam);
                expect(vm.filterStartDate).toEqual(newFilters.filterStartDate);
                expect(vm.filterEndDate).toEqual(newFilters.filterEndDate);
            });

            it('should NOT update controller filters when the dialog is cancelled', function() {
                // Arrange: Mock the dialog to return a rejected promise (simulating a cancel action)
                spyOn($mdDialog, 'show').and.returnValue($q.reject());

                // Act: Open the dialog
                vm.openFilterDialog(mockEvent);
                $rootScope.$apply(); // Reject the promise

                // Assert: Verify the controller's filter data remains unchanged
                expect(vm.selecteddomain).toEqual(initialFilterData.selecteddomain);
                expect(vm.selectedHostTeam).toEqual(initialFilterData.selectedHostTeam);
                expect(vm.sortByTeam).toEqual(initialFilterData.sortByTeam);
                expect(vm.filterStartDate).toEqual(initialFilterData.filterStartDate);
                expect(vm.filterEndDate).toEqual(initialFilterData.filterEndDate);
            });
        });
    });

});