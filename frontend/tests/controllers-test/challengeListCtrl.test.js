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
            expect(vm.noneCurrentChallenge).toBeTruthy();
            expect(vm.noneUpcomingChallenge).toBeTruthy();
            expect(vm.nonePastChallenge).toBeTruthy();
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
                expect(vm.currentList[i].start_zone).toEqual(zone.abbr(offset));
                offset = new Date(vm.currentList[i].end_date).getTimezoneOffset();
                expect(vm.currentList[i].end_zone).toEqual(zone.abbr(offset));

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
                expect(vm.upcomingList[i].start_zone).toEqual(zone.abbr(offset));
                offset = new Date(vm.upcomingList[i].end_date).getTimezoneOffset();
                expect(vm.upcomingList[i].end_zone).toEqual(zone.abbr(offset));

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
                expect(vm.pastList[i].start_zone).toEqual(zone.abbr(offset));
                offset = new Date(vm.pastList[i].end_date).getTimezoneOffset();
                expect(vm.pastList[i].end_zone).toEqual(zone.abbr(offset));

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


    });
});
