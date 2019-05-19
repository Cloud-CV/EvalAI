'use strict';

describe('Unit tests for Challenge List Controller', function () {
	beforeEach(angular.mock.module('evalai'));

	var $controller, createController, $rootScope, $scope, utilities, vm;

	beforeEach(inject(function(_$controller_, _$rootScope_, _utilities_,) {
        $controller = _$controller_;
        $rootScope = _$rootScope_;
        utilities = _utilities_;

        $scope = $rootScope.$new();
        createController = function () {
            return $controller('ChallengeListCtrl', { $scope: $scope });
        };
        vm = createController();
    }));

    describe('Global variables', function () {
        it('has default values', function () {
            spyOn(utilities, 'getData');
            spyOn(utilities, 'showLoader');

            vm = createController();
            expect(utilities.getData).toHaveBeenCalledWith('userKey');
            expect(vm.userKey).toEqual(utilities.getData('userKey'));
            expect(utilities.showLoader).toHaveBeenCalled();
            expect(vm.currentList).toEqual({});
            expect(vm.upcomingList).toEqual({});
            expect(vm.pastList).toEqual({});
            expect(vm.noneCurrentChallenge).toBeFalsy();
            expect(vm.noneUpcomingChallenge).toBeFalsy();
            expect(vm.nonePastChallenge).toBeFalsy();
            expect(vm.challengeCreator).toEqual({});
        });
    });

    describe('Unit tests for global backend calls', function () {
        var present_success, upcoming_success, past_success, success_response, error_response;

        beforeEach(function () {
            spyOn(utilities, 'hideLoader');
            spyOn(utilities, 'storeData');

            utilities.sendRequest = function (parameters) {
                if ((present_success == true && parameters.url == 'challenges/challenge/present') ||
                (upcoming_success == true && parameters.url == 'challenges/challenge/future') ||
                (past_success == true && parameters.url == 'challenges/challenge/past')) {
                    parameters.callback.onSuccess({
                        data: success_response
                    });
                } else if ((present_success == false && parameters.url == 'challenges/challenge/present') ||
                (upcoming_success == false && parameters.url == 'challenges/challenge/future') ||
                (past_success == false && parameters.url == 'challenges/challenge/past')){
                    parameters.callback.onError({
                        data: error_response
                    });
                }
            };
        });

        it('when no ongoing challenge found `challenges/challenge/present`', function () {
            present_success = true;
            upcoming_success = null;
            past_success = null;
            success_response = {
                results: []
            };
            vm = createController();
            expect(vm.currentList).toEqual(success_response.results);
            expect(vm.noneCurrentChallenge).toBeTruthy();
        });

        it('check description length and calculate timezone of ongoing challenge `challenges/challenge/present`', function () {
            present_success = true;
            upcoming_success = null;
            past_success = null;
            success_response = {
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
            expect(vm.currentList).toEqual(success_response.results);
            expect(vm.noneCurrentChallenge).toBeFalsy();

            var timezone = moment.tz.guess();
            for (var i in vm.currentList) {
                if (vm.currentList[i].description.length >= 50) {
                    expect(vm.currentList[i].isLarge).toEqual("...");
                } else {
                    expect(vm.currentList[i].isLarge).toEqual("");
                }
                var offset = new Date(vm.currentList[i].start_date).getTimezoneOffset();
                expect(vm.currentList[i].start_zone).toEqual(moment.tz.zone(timezone).abbr(offset));
                offset = new Date(vm.currentList[i].end_date).getTimezoneOffset();
                expect(vm.currentList[i].end_zone).toEqual(moment.tz.zone(timezone).abbr(offset));

                expect(vm.challengeCreator[vm.currentList[i].id]).toEqual(vm.currentList[i].creator.id);
                expect(utilities.storeData).toHaveBeenCalledWith("challengeCreator", vm.challengeCreator);
            }
        });

        it('ongoing challenge backend error `challenges/challenge/present`', function () {
            present_success = false; 
            upcoming_success = null;
            past_success = null;
            error_response = {
                error: 'error'
            };
            vm = createController();
            expect(utilities.hideLoader).toHaveBeenCalled();
        });

        it('when no upcoming `challenges/challenge/present`challenge found `challenges/challenge/future`', function () {
            upcoming_success = true;
            present_success = true;
            past_success = null;
            success_response = {
                results: []
            };
            vm = createController();
            expect(vm.upcomingList).toEqual(success_response.results);
            expect(vm.noneUpcomingChallenge).toBeTruthy();
        });

        it('check description length and calculate timezone of upcoming challenge `challenges/challenge/future`', function () {
            upcoming_success = true;
            present_success = true;
            past_success = null;
            success_response = {
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
            expect(vm.upcomingList).toEqual(success_response.results);
            expect(vm.noneUpcomingChallenge).toBeFalsy();

            var timezone = moment.tz.guess();
            for (var i in vm.upcomingList) {
                if (vm.upcomingList[i].description.length >= 50) {
                    expect(vm.upcomingList[i].isLarge).toEqual("...");
                } else {
                    expect(vm.upcomingList[i].isLarge).toEqual("");
                }
                var offset = new Date(vm.upcomingList[i].start_date).getTimezoneOffset();
                expect(vm.upcomingList[i].start_zone).toEqual(moment.tz.zone(timezone).abbr(offset));
                offset = new Date(vm.upcomingList[i].end_date).getTimezoneOffset();
                expect(vm.upcomingList[i].end_zone).toEqual(moment.tz.zone(timezone).abbr(offset));

                expect(vm.challengeCreator[vm.upcomingList[i].id]).toEqual(vm.upcomingList[i].creator.id);
                expect(utilities.storeData).toHaveBeenCalledWith("challengeCreator", vm.challengeCreator);
            }
        });

        it('upcoming challenge backend error `challenges/challenge/future`', function () {
            upcoming_success = false;
            present_success = true; 
            past_success = null;
            // success response for the ongoing challenge
            success_response = {
                results: []
            };
            error_response = {
                error: 'error'
            };
            vm = createController();
            expect(utilities.hideLoader).toHaveBeenCalled();
        });

        it('when no past challenge found `challenges/challenge/past`', function () {
            past_success = true;
            present_success = true;
            upcoming_success = true;
            success_response = {
                results: []
            };
            vm = createController();
            expect(vm.pastList).toEqual(success_response.results);
            expect(vm.nonePastChallenge).toBeTruthy();
        });

        it('check description length and calculate timezone of past challenge `challenges/challenge/past`', function () {
            past_success = true;
            present_success = true;
            upcoming_success = true;
            success_response = {
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
            expect(vm.pastList).toEqual(success_response.results);
            expect(vm.nonePastChallenge).toBeFalsy();

            var timezone = moment.tz.guess();
            for (var i in vm.pastList) {
                if (vm.pastList[i].description.length >= 50) {
                    expect(vm.pastList[i].isLarge).toEqual("...");
                } else {
                    expect(vm.pastList[i].isLarge).toEqual("");
                }
                var offset = new Date(vm.pastList[i].start_date).getTimezoneOffset();
                expect(vm.pastList[i].start_zone).toEqual(moment.tz.zone(timezone).abbr(offset));
                offset = new Date(vm.pastList[i].end_date).getTimezoneOffset();
                expect(vm.pastList[i].end_zone).toEqual(moment.tz.zone(timezone).abbr(offset));

                expect(vm.challengeCreator[vm.pastList[i].id]).toEqual(vm.pastList[i].creator.id);
                expect(utilities.storeData).toHaveBeenCalledWith("challengeCreator", vm.challengeCreator);
            }
            expect(utilities.hideLoader).toHaveBeenCalled();
        });

        it('past challenge backend error `challenges/challenge/past`', function () {
            past_success = false;
            present_success = true;
            upcoming_success = true;
            // success response for the ongoing and upcoming challenge
            success_response = {
                results: []
            };
            error_response = {
                error: 'error'
            };
            vm = createController();
            expect(utilities.hideLoader).toHaveBeenCalled();
        });
    });
});
