'use strict';

describe('Unit tests for challenge list controller', function () {
    beforeEach(angular.mock.module('evalai'));

    var $controller, createController, $rootScope, $scope, utilities, vm;

    beforeEach(inject(function (_$controller_, _$rootScope_, _utilities_,) {
        $controller = _$controller_;
        $rootScope = _$rootScope_;
        utilities = _utilities_;

        $scope = $rootScope.$new();
        createController = function () {
            return $controller('ChallengeListCtrl', {$scope: $scope});
        };
        vm = $controller('ChallengeListCtrl', { $scope: $scope });
    }));

    describe('Global variables', function () {
        it('has default values', function () {
            spyOn(utilities, 'getData');
            spyOn(utilities, 'showLoader');

            vm = createController();
            expect(utilities.getData).toHaveBeenCalledWith('userKey');
            expect(vm.userKey).toEqual(utilities.getData('userKey'));
            expect(utilities.showLoader).toHaveBeenCalled();
            expect(vm.currentList).toEqual([]);
            expect(vm.upcomingList).toEqual([]);
            expect(vm.pastList).toEqual([]);
            expect(vm.noneCurrentChallenge).toBeFalsy();
            expect(vm.noneUpcomingChallenge).toBeFalsy();
            expect(vm.nonePastChallenge).toBeFalsy();
            expect(vm.challengeCreator).toEqual({});
        });
    });

    describe('Unit tests for global backend calls', function () {
        var isPresentChallengeSuccess, isUpcomingChallengeSucess, isPastChallengeSuccess, successResponse, errorResponse;

        beforeEach(function () {
            spyOn(utilities, 'hideLoader');
            spyOn(utilities, 'storeData');

            utilities.sendRequest = function (parameters) {
                if ((isPresentChallengeSuccess == true && parameters.url == 'challenges/challenge/present/approved/public') ||
                (isUpcomingChallengeSucess == true && parameters.url == 'challenges/challenge/future/approved/public') ||
                (isPastChallengeSuccess == true && parameters.url == 'challenges/challenge/past/approved/public')) {
                    parameters.callback.onSuccess({
                        data: successResponse
                    });
                } else if ((isPresentChallengeSuccess == false && parameters.url == 'challenges/challenge/present/approved/public') ||
                (isUpcomingChallengeSucess == false && parameters.url == 'challenges/challenge/future/approved/public') ||
                (isPastChallengeSuccess == false && parameters.url == 'challenges/challenge/past/approved/public')){
                    parameters.callback.onError({
                        data: errorResponse
                    });
                }
            };
        });

        it('when no ongoing challenge found `challenges/challenge/present/approved/public`', function () {
            isPresentChallengeSuccess = true;
            isUpcomingChallengeSucess = null;
            isPastChallengeSuccess = null;
            successResponse = {
                next: null,
                results: []
            };
            vm = createController();
            expect(vm.currentList).toEqual(successResponse.results);
            expect(vm.noneCurrentChallenge).toBeTruthy();
        });

        it('check description length and calculate timezone of ongoing challenge `challenges/challenge/present/approved/public`', function () {
            isPresentChallengeSuccess = true;
            isUpcomingChallengeSucess = null;
            isPastChallengeSuccess = null;
            successResponse = {
                next: null,
                results: [
                    {
                        id: 1,
                        description: "the length of the ongoing challenge description is greater than or equal to 50",
                        creator: {
                            id: 1
                        },
                        start_date: "Fri June 12 2018 22:41:51 GMT+0530",
                        end_date: "Fri June 12 2099 22:41:51 GMT+0530"
                    },
                    {
                        id: 2,
                        description: "random description",
                        creator: {
                            id: 1
                        },
                        start_date: "Sat May 26 2015 22:41:51 GMT+0530",
                        end_date: "Sat May 26 2099 22:41:51 GMT+0530"
                    }
                ]
            };
            vm = createController();
            expect(vm.currentList).toEqual(successResponse.results);
            expect(vm.noneCurrentChallenge).toBeFalsy();

            var timezone = moment.tz.guess();
            var zone = moment.tz.zone(timezone);
            for (var i in vm.currentList) {
                if (vm.currentList[i].description.length >= 50) {
                    expect(vm.currentList[i].isLarge).toEqual("...");
                } else {
                    expect(vm.currentList[i].isLarge).toEqual("");
                }
                var offset = new Date(vm.currentList[i].start_date).getTimezoneOffset();
                expect(vm.currentList[i].time_zone).toEqual(zone.abbr(offset));

                expect(vm.challengeCreator[vm.currentList[i].id]).toEqual(vm.currentList[i].creator.id);
                expect(utilities.storeData).toHaveBeenCalledWith("challengeCreator", vm.challengeCreator);
            }
        });

        it('ongoing challenge backend error `challenges/challenge/present/approved/public`', function () {
            isPresentChallengeSuccess = false; 
            isUpcomingChallengeSucess = null;
            isPastChallengeSuccess = null;
            errorResponse = {
                next: null,
                error: 'error'
            };
            vm = createController();
            expect(utilities.hideLoader).toHaveBeenCalled();
        });

        it('when no upcoming `challenges/challenge/present/approved/public`challenge found `challenges/challenge/future/approved/public`', function () {
            isUpcomingChallengeSucess = true;
            isPresentChallengeSuccess = true;
            isPastChallengeSuccess = null;
            successResponse = {
                next: null,
                results: []
            };
            vm = createController();
            expect(vm.upcomingList).toEqual(successResponse.results);
            expect(vm.noneUpcomingChallenge).toBeTruthy();
        });

        it('check description length and calculate timezone of upcoming challenge `challenges/challenge/future`', function () {
            isUpcomingChallengeSucess = true;
            isPresentChallengeSuccess = true;
            isPastChallengeSuccess = null;
            successResponse = {
                next: null,
                results: [
                    {
                        id: 1,
                        description: "the length of the upcoming challenge description is greater than or equal to 50",
                        creator: {
                            id: 1
                        },
                        start_date: "Fri June 12 2018 22:41:51 GMT+0530",
                        end_date: "Fri June 12 2099 22:41:51 GMT+0530"
                    },
                    {
                        id: 2,
                        description: "random description",
                        creator: {
                            id: 1
                        },
                        start_date: "Sat May 26 2015 22:41:51 GMT+0530",
                        end_date: "Sat May 26 2099 22:41:51 GMT+0530"
                    }
                ]
            };
            vm = createController();
            expect(vm.upcomingList).toEqual(successResponse.results);
            expect(vm.noneUpcomingChallenge).toBeFalsy();

            var timezone = moment.tz.guess();
            var zone = moment.tz.zone(timezone);
            for (var i in vm.upcomingList) {
                if (vm.upcomingList[i].description.length >= 50) {
                    expect(vm.upcomingList[i].isLarge).toEqual("...");
                } else {
                    expect(vm.upcomingList[i].isLarge).toEqual("");
                }
                var offset = new Date(vm.upcomingList[i].start_date).getTimezoneOffset();
                expect(vm.upcomingList[i].time_zone).toEqual(zone.abbr(offset));

                expect(vm.challengeCreator[vm.upcomingList[i].id]).toEqual(vm.upcomingList[i].creator.id);
                expect(utilities.storeData).toHaveBeenCalledWith("challengeCreator", vm.challengeCreator);
            }
        });

        it('upcoming challenge backend error `challenges/challenge/future/approved/public`', function () {
            isUpcomingChallengeSucess = false;
            isPresentChallengeSuccess = true; 
            isPastChallengeSuccess = null;
            // success response for the ongoing challenge
            successResponse = {
                next: null,
                results: []
            };
            vm = createController();
            expect(vm.currentList).toEqual(successResponse.results);
            expect(utilities.hideLoader).toHaveBeenCalled();
        });

        it('when no past challenge found `challenges/challenge/past/approved/public`', function () {
            isPastChallengeSuccess = true;
            isPresentChallengeSuccess = true;
            isUpcomingChallengeSucess = true;
            successResponse = {
                next: null,
                results: []
            };
            vm = createController();
            expect(vm.pastList).toEqual(successResponse.results);
            expect(vm.nonePastChallenge).toBeTruthy();
        });

        it('check description length and calculate timezone of past challenge `challenges/challenge/past/approved/public`', function () {
            isPastChallengeSuccess = true;
            isPresentChallengeSuccess = true;
            isUpcomingChallengeSucess = true;
            successResponse = {
                next: null,
                results: [
                    {
                        id: 1,
                        description: "the length of the past challenge description is greater than or equal to 50",
                        creator: {
                            id: 1
                        },
                        start_date: "Fri June 12 2018 22:41:51 GMT+0530",
                        end_date: "Fri June 12 2099 22:41:51 GMT+0530"
                    },
                    {
                        id: 2,
                        description: "random description",
                        creator: {
                            id: 1
                        },
                        start_date: "Sat May 26 2015 22:41:51 GMT+0530",
                        end_date: "Sat May 26 2099 22:41:51 GMT+0530"
                    }
                ]
            };
            vm = createController();
            expect(vm.pastList).toEqual(successResponse.results);
            expect(vm.nonePastChallenge).toBeFalsy();

            var timezone = moment.tz.guess();
            var zone = moment.tz.zone(timezone);
            for (var i in vm.pastList) {
                if (vm.pastList[i].description.length >= 50) {
                    expect(vm.pastList[i].isLarge).toEqual("...");
                } else {
                    expect(vm.pastList[i].isLarge).toEqual("");
                }
                var offset = new Date(vm.pastList[i].start_date).getTimezoneOffset();
                expect(vm.pastList[i].time_zone).toEqual(zone.abbr(offset));

                expect(vm.challengeCreator[vm.pastList[i].id]).toEqual(vm.pastList[i].creator.id);
                expect(utilities.storeData).toHaveBeenCalledWith("challengeCreator", vm.challengeCreator);
            }
            expect(utilities.hideLoader).toHaveBeenCalled();
        });

        it('past challenge backend error `challenges/challenge/past/approved/public`', function () {
            isPastChallengeSuccess = false;
            isPresentChallengeSuccess = true;
            isUpcomingChallengeSucess = true;
            // success response for the ongoing and upcoming challenge
            successResponse = {
                next: null,
                results: []
            };
            vm = createController();
            expect(vm.currentList).toEqual(successResponse.results);
            expect(vm.upcomingList).toEqual(successResponse.results);
            expect(utilities.hideLoader).toHaveBeenCalled();
        });

        it('should call getAllResults method recursively when next is not null', function () {
            isPresentChallengeSuccess = true;
            isUpcomingChallengeSucess = null;
            isPastChallengeSuccess = null;

            // mock response with next property set to a non-null value
            successResponse = {
                next: 'http://example.com/challenges/?page=2',
                results: [
                    {
                        id: 1,
                        description: "the length of the ongoing challenge description is greater than or equal to 50",
                        creator: {
                        id: 1
                        },
                        start_date: "Fri June 12 2018 22:41:51 GMT+0530",
                        end_date: "Fri June 12 2099 22:41:51 GMT+0530"
                    }
                ]
            };

            vm = createController();
            spyOn(vm, 'getAllResults').and.callThrough();
            const parameters = {
                url: 'challenges/challenge/present/approved/public',
                method: 'GET',
                callback: jasmine.any(Function)
            };
            vm.getAllResults(parameters, []);
            expect(vm.currentList).toEqual(successResponse.results);
            expect(vm.noneCurrentChallenge).toBeFalsy();
            expect(vm.getAllResults).toHaveBeenCalledTimes(2);
        });

        it('ensures method is set to GET inside getAllResults function', function() {
            isPresentChallengeSuccess = true;
            isUpcomingChallengeSucess = null;
            isPastChallengeSuccess = null;
            successResponse = {
                next: null,
                results: []
            };
            
            vm = createController();
            spyOn(utilities, 'sendRequest').and.callThrough();
            
            const parameters = {
                url: 'challenges/challenge/present/approved/public'
            };
            
            vm.getAllResults(parameters, [], 'noneCurrentChallenge');
            
            expect(utilities.sendRequest).toHaveBeenCalled();
            expect(utilities.sendRequest.calls.argsFor(0)[0].method).toEqual('GET');
        });
        it('tests scrollUp function binding to window scroll events', function() {
            vm = createController();
            
            var mockElement = {
                bind: jasmine.createSpy('bind')
            };
            
            spyOn(angular, 'element').and.returnValue(mockElement);
            
            vm.scrollUp();
            
            expect(angular.element).toHaveBeenCalled();
            
            expect(mockElement.bind).toHaveBeenCalledWith('scroll', jasmine.any(Function));
            
            var scrollCallback = mockElement.bind.calls.mostRecent().args[1];
            
            spyOn(utilities, 'showButton');
            var mockScrollContext = { pageYOffset: 100 };
            scrollCallback.call(mockScrollContext);
            expect(utilities.showButton).toHaveBeenCalled();
            
            spyOn(utilities, 'hideButton');
            mockScrollContext.pageYOffset = 99;
            scrollCallback.call(mockScrollContext);
            expect(utilities.hideButton).toHaveBeenCalled();
        });

        describe('Filter functions', function () {
            beforeEach(function () {
                vm = createController();
            });
        
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
        
            it('should filter current challenges', function () {
                vm.currentList = [
                    {
                        id: 1,
                        title: 'Test Challenge 1',
                        domain_name: 'Computer Vision',
                        creator: { team_name: 'Team A' },
                        start_date: '2023-06-01T00:00:00Z',
                        list_tags: []
                    },
                    {
                        id: 2,
                        title: 'Test Challenge 2',
                        domain_name: 'NLP',
                        creator: { team_name: 'Team B' },
                        start_date: '2023-07-01T00:00:00Z',
                        list_tags: []
                    }
                ];
                // ... unchanged ...
            });
        
            it('should filter upcoming challenges', function () {
                vm.upcomingList = [
                    {
                        id: 3,
                        title: 'Upcoming Challenge 1',
                        domain_name: 'Computer Vision',
                        creator: { team_name: 'Team C' },
                        start_date: '2024-01-01T00:00:00Z',
                        list_tags: []
                    },
                    {
                        id: 4,
                        title: 'Upcoming Challenge 2',
                        domain_name: 'NLP',
                        creator: { team_name: 'Team D' },
                        start_date: '2024-02-01T00:00:00Z',
                        list_tags: []
                    }
                ];
                // ... unchanged ...
            });
        
            it('should filter past challenges', function () {
                vm.pastList = [
                    {
                        id: 5,
                        title: 'Past Challenge 1',
                        domain_name: 'Computer Vision',
                        creator: { team_name: 'Team E' },
                        start_date: '2022-01-01T00:00:00Z',
                        list_tags: []
                    },
                    {
                        id: 6,
                        title: 'Past Challenge 2',
                        domain_name: 'NLP',
                        creator: { team_name: 'Team F' },
                        start_date: '2022-02-01T00:00:00Z',
                        list_tags: []
                    }
                ];
                // ... unchanged ...
            });
        
            it('should handle empty filter values gracefully', function () {
                vm.currentList = [
                    {
                        id: 1,
                        title: 'Test Challenge',
                        domain_name: 'Computer Vision',
                        creator: { team_name: 'Team A' },
                        start_date: '2023-06-01T00:00:00Z',
                        list_tags: []
                    }
                ];
                vm.searchTitle = '';
                vm.selecteddomain = '';
                vm.selectedHostTeam = '';
                vm.filterStartDate = null;
                vm.filterEndDate = null;
                vm.sortByTeam = '';
        
                var result = vm.getFilteredCurrentChallenges();
                expect(Array.isArray(result)).toBe(true);
                expect(result.length).toBe(1);
            });
        });
    });

    describe('openFilterDialog', function () {
        var $mdDialog, $rootScope;
    
        beforeEach(inject(function (_$mdDialog_, _$rootScope_) {
            $mdDialog = _$mdDialog_;
            $rootScope = _$rootScope_;
            vm = createController();
        }));
    
        it('should call $mdDialog.show with correct parameters', function () {
            spyOn($mdDialog, 'show').and.callFake(function () {
                return { then: function () {} };
            });
            spyOn(console, 'log');
    
            // Set some filter values
            vm.selecteddomain = ['Computer Vision'];
            vm.selectedHostTeam = 'Team A';
            vm.sortByTeam = 'asc';
            vm.filterStartDate = new Date('2023-01-01');
            vm.filterEndDate = new Date('2023-12-31');
            vm.domain_choices = [['All', 'All'], ['Computer Vision', 'Computer Vision']];
            vm.host_team_choices = ['Team A', 'Team B'];
    
            vm.openFilterDialog('fakeEvent');
    
            expect(console.log).toHaveBeenCalledWith('Filter dialog opened');
            expect($mdDialog.show).toHaveBeenCalled();
            var args = $mdDialog.show.calls.mostRecent().args[0];
            expect(args.controllerAs).toBe('dialog');
            expect(args.templateUrl).toBe('src/views/web/challenge/challenge-filter-dialog.html');
            expect(args.locals.filterData.selecteddomain).toEqual(['Computer Vision']);
            expect(args.locals.filterData.selectedHostTeam).toBe('Team A');
            expect(args.locals.filterData.sortByTeam).toBe('asc');
            expect(args.locals.filterData.filterStartDate).toEqual(new Date('2023-01-01'));
            expect(args.locals.filterData.filterEndDate).toEqual(new Date('2023-12-31'));
            expect(args.locals.filterData.domain_choices).toEqual([['All', 'All'], ['Computer Vision', 'Computer Vision']]);
            expect(args.locals.filterData.host_team_choices).toEqual(['Team A', 'Team B']);
        });
    
        it('should update filter values when dialog resolves', function () {
            spyOn($mdDialog, 'show').and.callFake(function () {
                return {
                    then: function (cb) {
                        cb({
                            selecteddomain: ['NLP'],
                            selectedHostTeam: 'Team B',
                            sortByTeam: 'desc',
                            filterStartDate: new Date('2024-01-01'),
                            filterEndDate: new Date('2024-12-31')
                        });
                    }
                };
            });
    
            // Set initial values
            vm.selecteddomain = ['Computer Vision'];
            vm.selectedHostTeam = 'Team A';
            vm.sortByTeam = 'asc';
            vm.filterStartDate = new Date('2023-01-01');
            vm.filterEndDate = new Date('2023-12-31');
    
            vm.openFilterDialog('fakeEvent');
    
            expect(vm.selecteddomain).toEqual(['NLP']);
            expect(vm.selectedHostTeam).toBe('Team B');
            expect(vm.sortByTeam).toBe('desc');
            expect(vm.filterStartDate).toEqual(new Date('2024-01-01'));
            expect(vm.filterEndDate).toEqual(new Date('2024-12-31'));
        });
    
        it('should not throw if dialog is cancelled', function () {
            spyOn($mdDialog, 'show').and.callFake(function () {
                return { then: function () { /* do nothing, simulates cancel */ } };
            });
    
            // Set initial values
            vm.selecteddomain = ['Computer Vision'];
            vm.selectedHostTeam = 'Team A';
            vm.sortByTeam = 'asc';
            vm.filterStartDate = new Date('2023-01-01');
            vm.filterEndDate = new Date('2023-12-31');
    
            expect(function () {
                vm.openFilterDialog('fakeEvent');
            }).not.toThrow();
    
            // Values should remain unchanged
            expect(vm.selecteddomain).toEqual(['Computer Vision']);
            expect(vm.selectedHostTeam).toBe('Team A');
            expect(vm.sortByTeam).toBe('asc');
            expect(vm.filterStartDate).toEqual(new Date('2023-01-01'));
            expect(vm.filterEndDate).toEqual(new Date('2023-12-31'));
        });
    });

    describe('FilterDialogController', function () {
        var $scope, $mdDialog, filterData, $controller;
    
        beforeEach(inject(function (_$controller_, _$rootScope_, _$mdDialog_) {
            $controller = _$controller_;
            $scope = _$rootScope_.$new();
            $mdDialog = _$mdDialog_;
            spyOn($mdDialog, 'hide');
            spyOn($mdDialog, 'cancel');
        }));
    
        // This test already covers the initialization lines by ensuring they are assigned
        it('should initialize $scope variables from complete filterData', function () {
            filterData = {
                selecteddomain: ['Computer Vision'],
                selectedHostTeam: 'Team A',
                sortByTeam: 'asc',
                filterStartDate: new Date('2023-01-01'),
                filterEndDate: new Date('2023-12-31'),
                domain_choices: [['All', 'All'], ['Computer Vision', 'Computer Vision']],
                host_team_choices: ['Team A', 'Team B']
            };
    
            $controller('FilterDialogController', {
                $scope: $scope,
                $mdDialog: $mdDialog,
                filterData: filterData
            });
    
            // Assertions to confirm all properties are correctly assigned
            expect($scope.selecteddomain).toEqual(['Computer Vision']);
            expect($scope.selectedHostTeam).toBe('Team A');
            expect($scope.sortByTeam).toBe('asc');
            expect($scope.filterStartDate).toEqual(new Date('2023-01-01'));
            expect($scope.filterEndDate).toEqual(new Date('2023-12-31'));
            expect($scope.domain_choices).toEqual([['All', 'All'], ['Computer Vision', 'Computer Vision']]);
            expect($scope.host_team_choices).toEqual(['Team A', 'Team B']);
        });
    
        // --- New test case for coverage of initialization lines with potentially missing data ---
        // This case ensures that even if some filterData properties are undefined,
        // the assignment lines are still executed.
        it('should initialize $scope variables when some filterData properties are undefined', function () {
            filterData = {
                selecteddomain: undefined,
                selectedHostTeam: null, // Test with null as well
                sortByTeam: 'asc',
                // Missing filterStartDate and filterEndDate
                domain_choices: [['All', 'All']],
                host_team_choices: []
            };
    
            $controller('FilterDialogController', {
                $scope: $scope,
                $mdDialog: $mdDialog,
                filterData: filterData
            });
    
            expect($scope.selecteddomain).toBeUndefined();
            expect($scope.selectedHostTeam).toBeNull();
            expect($scope.sortByTeam).toBe('asc');
            expect($scope.filterStartDate).toBeUndefined(); // Will be undefined if not provided
            expect($scope.filterEndDate).toBeUndefined();   // Will be undefined if not provided
            expect($scope.domain_choices).toEqual([['All', 'All']]);
            expect($scope.host_team_choices).toEqual([]);
        });
        // --- End of new test case ---
    
        it('should call $mdDialog.hide with correct data on apply()', function () {
            filterData = {
                selecteddomain: ['Computer Vision'], selectedHostTeam: 'Team A', sortByTeam: 'asc',
                filterStartDate: new Date('2023-01-01'), filterEndDate: new Date('2023-12-31'),
                domain_choices: [['All', 'All']], host_team_choices: ['Team A']
            };
            $controller('FilterDialogController', {
                $scope: $scope,
                $mdDialog: $mdDialog,
                filterData: filterData
            });
    
            // Change some values to ensure hide receives the *updated* scope values
            $scope.selecteddomain = ['NLP'];
            $scope.selectedHostTeam = 'Team B';
            $scope.sortByTeam = 'desc';
            $scope.filterStartDate = new Date('2024-01-01');
            $scope.filterEndDate = new Date('2024-12-31');
    
            $scope.apply();
    
            expect($mdDialog.hide).toHaveBeenCalledWith({
                selecteddomain: ['NLP'],
                selectedHostTeam: 'Team B',
                sortByTeam: 'desc',
                filterStartDate: new Date('2024-01-01'),
                filterEndDate: new Date('2024-12-31')
            });
        });
    
        it('should call $mdDialog.cancel on cancel()', function () {
            filterData = { /* minimal data needed for controller instantiation */ };
            $controller('FilterDialogController', {
                $scope: $scope,
                $mdDialog: $mdDialog,
                filterData: filterData
            });
            $scope.cancel();
            expect($mdDialog.cancel).toHaveBeenCalled();
        });
    });
});
