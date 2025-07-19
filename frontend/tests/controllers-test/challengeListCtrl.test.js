'use strict';

describe('Unit tests for challenge list controller', function () {
    beforeEach(angular.mock.module('evalai'));

    var $controller, createController, $rootScope, $scope, utilities, vm, $filter;

    beforeEach(inject(function (_$controller_, _$rootScope_, _utilities_, _$filter_) {
        $controller = _$controller_;
        $rootScope = _$rootScope_;
        utilities = _utilities_;
        $filter = _$filter_;

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

        it('should reset all filters to default values', function() {
            vm.selecteddomain = ['domain1'];
            vm.searchTitle = ['title'];
            vm.selectedHostTeam = 'hostTeam';
            vm.sortByTeam = 'asc';
            vm.filterStartDate = '2024-01-01';
            vm.filterEndDate = '2024-12-31';

            vm.resetFilter();

            expect(vm.selecteddomain).toEqual([]);
            expect(vm.searchTitle).toEqual([]);
            expect(vm.selectedHostTeam).toBe('');
            expect(vm.sortByTeam).toBe('');
            expect(vm.filterStartDate).toBeNull();
            expect(vm.filterEndDate).toBeNull();
        });

        it('should filter current challenges using all filters', function() {
            vm.currentList = [{id: 1}, {id: 2}];
            vm.searchTitle = ['title'];
            vm.selecteddomain = ['domain'];
            vm.selectedHostTeam = 'hostTeam';
            vm.sortByTeam = 'asc';
            vm.filterStartDate = '2024-01-01';
            vm.filterEndDate = '2024-12-31';

            // Mock $filter to just return the input array for each filter
            spyOn($filter).and.callFake(function() {
                return function(arr) { return arr; };
            });

            var filtered = vm.getFilteredCurrentChallenges();
            expect(filtered).toBe(vm.currentList);
        });

        it('should filter upcoming challenges using all filters', function() {
            vm.upcomingList = [{id: 3}, {id: 4}];
            vm.searchTitle = ['title'];
            vm.selecteddomain = ['domain'];
            vm.selectedHostTeam = 'hostTeam';
            vm.sortByTeam = 'asc';
            vm.filterStartDate = '2024-01-01';
            vm.filterEndDate = '2024-12-31';

            spyOn($filter).and.callFake(function() {
                return function(arr) { return arr; };
            });

            var filtered = vm.getFilteredUpcomingChallenges();
            expect(filtered).toBe(vm.upcomingList);
        });

        it('should filter past challenges using all filters', function() {
            vm.pastList = [{id: 5}, {id: 6}];
            vm.searchTitle = ['title'];
            vm.selecteddomain = ['domain'];
            vm.selectedHostTeam = 'hostTeam';
            vm.sortByTeam = 'asc';
            vm.filterStartDate = '2024-01-01';
            vm.filterEndDate = '2024-12-31';

            spyOn($filter).and.callFake(function() {
                return function(arr) { return arr; };
            });

            var filtered = vm.getFilteredPastChallenges();
            expect(filtered).toBe(vm.pastList);
        });
    });

    describe('Unit tests for filter dialog', function () {
        var $mdDialog, $controller, $rootScope, $scope, vm;

        beforeEach(inject(function (_$mdDialog_, _$controller_, _$rootScope_) {
            $mdDialog = _$mdDialog_;
            $controller = _$controller_;
            $rootScope = _$rootScope_;
            $scope = $rootScope.$new();
            vm = createController();
        }));

        it('should open filter dialog and update filters on dialog close', function (done) {
            // Arrange
            var ev = {};
            var filters = {
                selecteddomain: ['domain1'],
                selectedHostTeam: 'host1',
                sortByTeam: 'asc',
                filterStartDate: '2024-01-01',
                filterEndDate: '2024-12-31'
            };
            spyOn($mdDialog, 'show').and.returnValue(Promise.resolve(filters));
            // Set some initial values
            vm.selecteddomain = [];
            vm.selectedHostTeam = '';
            vm.sortByTeam = '';
            vm.filterStartDate = null;
            vm.filterEndDate = null;

            // Act
            vm.openFilterDialog(ev);

            // Assert
            setTimeout(function () {
                expect($mdDialog.show).toHaveBeenCalled();
                expect(vm.selecteddomain).toEqual(filters.selecteddomain);
                expect(vm.selectedHostTeam).toEqual(filters.selectedHostTeam);
                expect(vm.sortByTeam).toEqual(filters.sortByTeam);
                expect(vm.filterStartDate).toEqual(filters.filterStartDate);
                expect(vm.filterEndDate).toEqual(filters.filterEndDate);
                done();
            }, 0);
        });

        it('should open filter dialog and do nothing if dialog is cancelled', function (done) {
            var ev = {};
            spyOn($mdDialog, 'show').and.returnValue(Promise.reject());
            // Set some initial values
            vm.selecteddomain = ['domain1'];
            vm.selectedHostTeam = 'host1';
            vm.sortByTeam = 'asc';
            vm.filterStartDate = '2024-01-01';
            vm.filterEndDate = '2024-12-31';

            vm.openFilterDialog(ev);

            setTimeout(function () {
                // Values should remain unchanged
                expect(vm.selecteddomain).toEqual(['domain1']);
                expect(vm.selectedHostTeam).toEqual('host1');
                expect(vm.sortByTeam).toEqual('asc');
                expect(vm.filterStartDate).toEqual('2024-01-01');
                expect(vm.filterEndDate).toEqual('2024-12-31');
                done();
            }, 0);
        });

        it('should initialize FilterDialogController with filterData', function () {
            var filterData = {
                selecteddomain: ['domain1'],
                selectedHostTeam: 'host1',
                sortByTeam: 'asc',
                filterStartDate: '2024-01-01',
                filterEndDate: '2024-12-31',
                domain_choices: [['All', 'All']],
                host_team_choices: ['host1']
            };
            var ctrlScope = $rootScope.$new();
            $controller('FilterDialogController', {
                $scope: ctrlScope,
                $mdDialog: $mdDialog,
                filterData: filterData
            });
            expect(ctrlScope.selecteddomain).toEqual(filterData.selecteddomain);
            expect(ctrlScope.selectedHostTeam).toEqual(filterData.selectedHostTeam);
            expect(ctrlScope.sortByTeam).toEqual(filterData.sortByTeam);
            expect(ctrlScope.filterStartDate).toEqual(filterData.filterStartDate);
            expect(ctrlScope.filterEndDate).toEqual(filterData.filterEndDate);
            expect(ctrlScope.domain_choices).toEqual(filterData.domain_choices);
            expect(ctrlScope.host_team_choices).toEqual(filterData.host_team_choices);
        });

        it('should call $mdDialog.hide with correct filters on apply', function () {
            var filterData = {
                selecteddomain: ['domain1'],
                selectedHostTeam: 'host1',
                sortByTeam: 'asc',
                filterStartDate: '2024-01-01',
                filterEndDate: '2024-12-31',
                domain_choices: [['All', 'All']],
                host_team_choices: ['host1']
            };
            var ctrlScope = $rootScope.$new();
            var mockMdDialog = { hide: jasmine.createSpy('hide') };
            $controller('FilterDialogController', {
                $scope: ctrlScope,
                $mdDialog: mockMdDialog,
                filterData: filterData
            });
            ctrlScope.apply();
            expect(mockMdDialog.hide).toHaveBeenCalledWith({
                selecteddomain: filterData.selecteddomain,
                selectedHostTeam: filterData.selectedHostTeam,
                sortByTeam: filterData.sortByTeam,
                filterStartDate: filterData.filterStartDate,
                filterEndDate: filterData.filterEndDate
            });
        });

        it('should call $mdDialog.cancel on cancel', function () {
            var filterData = {
                selecteddomain: [],
                selectedHostTeam: '',
                sortByTeam: '',
                filterStartDate: null,
                filterEndDate: null,
                domain_choices: [],
                host_team_choices: []
            };
            var ctrlScope = $rootScope.$new();
            var mockMdDialog = { cancel: jasmine.createSpy('cancel') };
            $controller('FilterDialogController', {
                $scope: ctrlScope,
                $mdDialog: mockMdDialog,
                filterData: filterData
            });
            ctrlScope.cancel();
            expect(mockMdDialog.cancel).toHaveBeenCalled();
        });
    });
});
