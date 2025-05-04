'use strict';

describe('Unit tests for challenge list controller', function () {
    beforeEach(angular.mock.module('evalai'));

    var $controller, createController, $rootScope, $scope, utilities, vm, $httpBackend;

    beforeEach(inject(function (_$controller_, _$rootScope_, _utilities_, _$httpBackend_) {
        $controller = _$controller_;
        $rootScope = _$rootScope_;
        utilities = _utilities_;
        $httpBackend = _$httpBackend_;

        $scope = $rootScope.$new();
        createController = function () {
            return $controller('ChallengeListCtrl', { $scope: $scope });
        };
        vm = $controller('ChallengeListCtrl', { $scope: $scope });
    }));

    describe('Global variables initialization', function () {
        it('should initialize global variables with default values', function () {
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

    describe('Backend calls for challenge data', function () {
        var isPresentChallengeSuccess, isUpcomingChallengeSuccess, isPastChallengeSuccess, successResponse, errorResponse;

        beforeEach(function () {
            spyOn(utilities, 'hideLoader');
            spyOn(utilities, 'storeData');

            utilities.sendRequest = function (parameters) {
                if ((isPresentChallengeSuccess === true && parameters.url === 'challenges/challenge/present/approved/public') ||
                    (isUpcomingChallengeSuccess === true && parameters.url === 'challenges/challenge/future/approved/public') ||
                    (isPastChallengeSuccess === true && parameters.url === 'challenges/challenge/past/approved/public')) {
                    parameters.callback.onSuccess({
                        data: successResponse
                    });
                } else if ((isPresentChallengeSuccess === false && parameters.url === 'challenges/challenge/present/approved/public') ||
                    (isUpcomingChallengeSuccess === false && parameters.url === 'challenges/challenge/future/approved/public') ||
                    (isPastChallengeSuccess === false && parameters.url === 'challenges/challenge/past/approved/public')) {
                    parameters.callback.onError({
                        data: errorResponse
                    });
                }
            };
        });

        it('should handle the case when no ongoing challenge is found', function () {
            isPresentChallengeSuccess = true;
            successResponse = { next: null, results: [] };
            vm = createController();
            expect(vm.currentList).toEqual(successResponse.results);
            expect(vm.noneCurrentChallenge).toBeTruthy();
        });

        it('should check description length and timezone for ongoing challenges', function () {
            isPresentChallengeSuccess = true;
            successResponse = {
                next: null,
                results: [
                    {
                        id: 1,
                        description: "A description with more than 50 characters, so it should show an ellipsis at the end...",
                        creator: { id: 1 },
                        start_date: "Fri June 12 2018 22:41:51 GMT+0530",
                        end_date: "Fri June 12 2099 22:41:51 GMT+0530"
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

        it('should handle error when fetching ongoing challenges', function () {
            isPresentChallengeSuccess = false;
            errorResponse = { next: null, error: 'error' };
            vm = createController();
            expect(utilities.hideLoader).toHaveBeenCalled();
        });

        it('should handle the case when no upcoming challenges are found', function () {
            isUpcomingChallengeSuccess = true;
            successResponse = { next: null, results: [] };
            vm = createController();
            expect(vm.upcomingList).toEqual(successResponse.results);
            expect(vm.noneUpcomingChallenge).toBeTruthy();
        });

        it('should check description length and timezone for upcoming challenges', function () {
            isUpcomingChallengeSuccess = true;
            successResponse = {
                next: null,
                results: [
                    {
                        id: 1,
                        description: "Upcoming challenge description with more than 50 characters...",
                        creator: { id: 1 },
                        start_date: "Fri June 12 2018 22:41:51 GMT+0530",
                        end_date: "Fri June 12 2099 22:41:51 GMT+0530"
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

        it('should handle error when fetching upcoming challenges', function () {
            isUpcomingChallengeSuccess = false;
            successResponse = { next: null, results: [] };
            vm = createController();
            expect(vm.upcomingList).toEqual(successResponse.results);
            expect(utilities.hideLoader).toHaveBeenCalled();
        });

        it('should handle the case when no past challenges are found', function () {
            isPastChallengeSuccess = true;
            successResponse = { next: null, results: [] };
            vm = createController();
            expect(vm.pastList).toEqual(successResponse.results);
            expect(vm.nonePastChallenge).toBeTruthy();
        });

        it('should check description length and timezone for past challenges', function () {
            isPastChallengeSuccess = true;
            successResponse = {
                next: null,
                results: [
                    {
                        id: 1,
                        description: "Past challenge description with more than 50 characters...",
                        creator: { id: 1 },
                        start_date: "Fri June 12 2018 22:41:51 GMT+0530",
                        end_date: "Fri June 12 2099 22:41:51 GMT+0530"
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

        it('should handle error when fetching past challenges', function () {
            isPastChallengeSuccess = false;
            successResponse = { next: null, results: [] };
            vm = createController();
            expect(vm.currentList).toEqual(successResponse.results);
            expect(vm.upcomingList).toEqual(successResponse.results);
            expect(utilities.hideLoader).toHaveBeenCalled();
        });

        it('should call getAllResults recursively when next is not null', function () {
            isPresentChallengeSuccess = true;
            successResponse = {
                next: 'http://example.com/challenges/?page=2',
                results: [
                    {
                        id: 1,
                        description: "Challenge description",
                        creator: { id: 1 },
                        start_date: "Fri June 12 2018 22:41:51 GMT+0530",
                        end_date: "Fri June 12 2099 22:41:51 GMT+0530"
                    }
                ]
            };
            vm = createController();
            expect(vm.getAllResults).toHaveBeenCalled();
        });
    });
});
