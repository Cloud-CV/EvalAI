'use strict';

describe('Unit tests for featured challenge controller', function () {
    beforeEach(angular.mock.module('evalai'));

    var $controller, createController, $rootScope, $state, $stateParams, $scope, utilities, vm;

    beforeEach(inject(function (_$controller_, _$rootScope_, _$stateParams_, _$state_, _utilities_, _moment_) {
        $controller = _$controller_;
        $rootScope = _$rootScope_;
        $state = _$state_;
        utilities = _utilities_;
        $stateParams = _$stateParams_;

        $scope = $rootScope.$new();
        createController = function () {
            return $controller('FeaturedChallengeCtrl', {$scope: $scope});
        };
        vm = $controller('FeaturedChallengeCtrl', { $scope: $scope });
    }));

    describe('Global variables', function () {
        it('has default values', function () {
            vm = createController();
            expect(vm.challengeId).toEqual($stateParams.challengeId);
            expect(vm.phaseSplitId).toEqual($stateParams.phaseSplitId);
            expect(vm.phaseId).toBeNull();
            expect(vm.wrnMsg).toEqual({});
            expect(vm.page).toEqual({});
            expect(vm.phases).toEqual({});
            expect(vm.phaseSplits).toEqual({});
            expect(vm.isValid).toEqual({});
            expect(vm.isActive).toBeFalsy();
            expect(vm.showUpdate).toBeFalsy();
            expect(vm.showLeaderboardUpdate).toBeFalsy();
            expect(vm.poller).toBeNull();

            // variables for loader of existing teams
            expect(vm.isExistLoader).toBeFalsy();
            expect(vm.loaderTitle).toEqual('');
        });
    });

    describe('Unit tests for global backend calls', function () {
        var challengeSuccess, challengePhaseSuccess, challengePhaseSplitSuccess, successResponse;
        var errorResponse = {
            detail: 'error'
        };

        beforeEach(function () {
            spyOn($state, 'go');
            spyOn(utilities, 'storeData');
            spyOn(utilities, 'hideLoader');

            utilities.sendRequest = function (parameters) {
                if ((challengeSuccess == true && parameters.url == 'challenges/challenge/undefined/') ||
                (challengePhaseSuccess == true && parameters.url == 'challenges/challenge/undefined/challenge_phase') ||
                (challengePhaseSplitSuccess == true && parameters.url == 'challenges/undefined/challenge_phase_split')) {
                    parameters.callback.onSuccess({
                        data: successResponse,
                        status: 200
                    });
                } else if ((challengeSuccess == false && parameters.url == 'challenges/challenge/undefined/') ||
                (challengePhaseSuccess == false && parameters.url == 'challenges/challenge/undefined/challenge_phase') ||
                (challengePhaseSplitSuccess == false && parameters.url == 'challenges/undefined/challenge_phase_split')) {
                    parameters.callback.onError({
                        data: errorResponse
                    });
                }
            };
        });

        it('get the details of the particular challenge `challenges/challenge/<challenge_id>/`', function () {
            challengeSuccess = true;
            challengePhaseSuccess = null;
            challengePhaseSplitSuccess = null;
            successResponse = {
                is_active: true,
                image: 'logo.png'
            };
            vm = createController();
            expect(vm.page).toEqual(successResponse);
            expect(vm.isActive).toEqual(successResponse.is_active);
        });

        it('when challenge logo image is null `challenges/challenge/<challenge_id>/`', function () {
            challengeSuccess = true;
            challengePhaseSuccess = null;
            challengePhaseSplitSuccess = null;
            successResponse = {
                is_active: true,
                image: null
            };
            vm = createController();
            expect(vm.page).toEqual(successResponse);
            expect(vm.isActive).toEqual(successResponse.is_active);
            expect(vm.page.image).toEqual("dist/images/logo.png");
        });

        it('get challenge backend error `challenges/challenge/<challenge_id>/`', function () {
            challengeSuccess = false;
            challengePhaseSuccess = null;
            challengePhaseSplitSuccess = null;
            vm = createController();
            expect(utilities.storeData).toHaveBeenCalledWith('emailError', errorResponse.detail);
            expect($state.go).toHaveBeenCalledWith('web.permission-denied');
            expect(utilities.hideLoader).toHaveBeenCalled();
        });

        it('get the details of the particular challenge phase `challenges/challenge/<challenge_id>/challenge_phase`', function () {
            challengeSuccess = null;
            challengePhaseSuccess = true;
            challengePhaseSplitSuccess = null;
            successResponse = {
                id: 1,
                name: "Challenge phase",
                description: "Challenge phase description"
            };
            vm = createController();
            expect(vm.phases).toEqual(successResponse);
            expect(utilities.hideLoader).toHaveBeenCalled();
        });

        it('get challenge phase backend error `challenges/challenge/<challenge_id>/challenge_phase`', function () {
            challengeSuccess = null;
            challengePhaseSuccess = false;
            challengePhaseSplitSuccess = null;
            vm = createController();
            expect(utilities.storeData).toHaveBeenCalledWith('emailError', errorResponse.detail);
            expect($state.go).toHaveBeenCalledWith('web.permission-denied');
            expect(utilities.hideLoader).toHaveBeenCalled();
        });

        it('get the details of the particular challenge phase split `challenges/<challenge_id>/challenge_phase_split`', function () {
            challengeSuccess = null;
            challengePhaseSuccess = null;
            challengePhaseSplitSuccess = true;
            successResponse = {
                id: 1,
                challenge_phase: "Challenge phase object",
                dataset_split: "Dataset split object",
                visibility: "public"
            };
            vm = createController();
            expect(vm.phaseSplits).toEqual(successResponse);
            expect(utilities.hideLoader).toHaveBeenCalled();
        });

        it('get challenge phase split backend error `challenges/<challenge_id>/challenge_phase_split`', function () {
            challengeSuccess = null;
            challengePhaseSuccess = null;
            challengePhaseSplitSuccess = false;
            vm = createController();
            expect(utilities.storeData).toHaveBeenCalledWith('emailError', errorResponse.detail);
            expect($state.go).toHaveBeenCalledWith('web.permission-denied');
            expect(utilities.hideLoader).toHaveBeenCalled();
        });
    });

    describe('Unit tests for getLeaderboard function \
    `jobs/challenge_phase_split/<phase_split_id>/leaderboard/?page_size=1000`', function () {
        var success, successResponse, errorResponse;

        beforeEach(function () {
            spyOn(vm, 'startLoader');
            spyOn(vm, 'stopLoader');
            spyOn(angular, 'element');

            utilities.sendRequest = function (parameters) {
                if (success) {
                    parameters.callback.onSuccess({
                        data: successResponse
                    });
                } else {
                    parameters.callback.onError({
                        data: errorResponse
                    });
                }
            };
        });

        it('successfully get the leaderboard', function () {
            success = true;
            successResponse = {
                results: {
                    duration: 'year',
                    results: [
                        {
                            id: 1,
                            submission__submitted_at: (new Date() - new Date().setFullYear(new Date().getFullYear() - 1)),
                        },
                    ]
                },
            };
            var phaseSplitId = 1;
            vm.getLeaderboard(phaseSplitId);
            expect(vm.isResult).toBeTruthy();
            expect(angular.element).toHaveBeenCalledWith('.exist-team-card');
            expect(vm.startLoader).toHaveBeenCalledWith('Loading Leaderboard Items');
            expect(vm.leaderboard).toEqual(successResponse.results);
            expect(vm.phase_name).toEqual(vm.phaseSplitId);
            expect(vm.stopLoader).toHaveBeenCalled();
        });

        it('getLeaderboard backend error', function () {
            success = false;
            errorResponse = 'error';
            var phaseSplitId = 1;
            vm.getLeaderboard(phaseSplitId);
            expect(vm.isResult).toEqual(true);
            expect(vm.startLoader).toHaveBeenCalledWith('Loading Leaderboard Items');
            expect(vm.leaderboard.error).toEqual(errorResponse);
            expect(vm.stopLoader).toHaveBeenCalled();
        });
    });

    describe('Unit tests for leaderboard submission__submitted_at formatting', function () {
        var $controller, $rootScope, $scope, utilities, vm, moment;
    
        beforeEach(inject(function (_$controller_, _$rootScope_, _utilities_, _moment_) {
            $controller = _$controller_;
            $rootScope = _$rootScope_;
            utilities = _utilities_;
            moment = _moment_;
            $scope = $rootScope.$new();
            vm = $controller('FeaturedChallengeCtrl', { $scope: $scope });
            spyOn(vm, 'startLoader');
            spyOn(vm, 'stopLoader');
            spyOn(angular, 'element');
        }));
    
        function leaderboardWithSubmissionAt(date) {
            return {
                results: {
                    results: [
                        { id: 1, submission__submitted_at: date }
                    ]
                }
            };
        }
    
        it('should set timeSpan to "months" for 1 year ago', function () {
            var oneYearAgo = moment().subtract(1, 'years').toDate();
            var response = leaderboardWithSubmissionAt(oneYearAgo);
    
            utilities.sendRequest = function (parameters) {
                parameters.callback.onSuccess({ data: response.results });
            };
    
            vm.getLeaderboard(1);
                
            expect(vm.leaderboard[0].timeSpan).toBe('months');
        });
    
        it('should set timeSpan to "years" for 2 years ago', function () {
            var twoYearsAgo = moment().subtract(2, 'years').toDate();
            var response = leaderboardWithSubmissionAt(twoYearsAgo);
    
            utilities.sendRequest = function (parameters) {
                parameters.callback.onSuccess({ data: response.results });
            };
    
            vm.getLeaderboard(1);
    
            expect(vm.leaderboard[0].timeSpan).toBe('years');
        });
    
        it('should set timeSpan to "days" for 1 month ago', function () {
            var oneMonthAgo = moment().subtract(1, 'months').toDate();
            var response = leaderboardWithSubmissionAt(oneMonthAgo);
    
            utilities.sendRequest = function (parameters) {
                parameters.callback.onSuccess({ data: response.results });
            };
    
            vm.getLeaderboard(1);
             
            expect(vm.leaderboard[0].timeSpan).toBe('month')
        });
    
        it('should set timeSpan to "months" for 3 months ago', function () {
            var threeMonthsAgo = moment().subtract(3, 'months').toDate();
            var response = leaderboardWithSubmissionAt(threeMonthsAgo);
    
            utilities.sendRequest = function (parameters) {
                parameters.callback.onSuccess({ data: response.results });
            };
    
            vm.getLeaderboard(1);
    
            expect(vm.leaderboard[0].timeSpan).toBe('months');
        });
    
        it('should set timeSpan to "day" for 1 day ago', function () {
            var oneDayAgo = moment().subtract(1, 'days').toDate();
            var response = leaderboardWithSubmissionAt(oneDayAgo);
    
            utilities.sendRequest = function (parameters) {
                parameters.callback.onSuccess({ data: response.results });
            };
    
            vm.getLeaderboard(1);
    
            expect(vm.leaderboard[0].timeSpan).toBe('day');
        });
    
        it('should set timeSpan to "days" for 5 days ago', function () {
            var fiveDaysAgo = moment().subtract(5, 'days').toDate();
            var response = leaderboardWithSubmissionAt(fiveDaysAgo);
    
            utilities.sendRequest = function (parameters) {
                parameters.callback.onSuccess({ data: response.results });
            };
    
            vm.getLeaderboard(1);
    
            expect(vm.leaderboard[0].timeSpan).toBe('days');
        });
    
        it('should set timeSpan to "hour" for 1 hour ago', function () {
            var oneHourAgo = moment().subtract(1, 'hours').toDate();
            var response = leaderboardWithSubmissionAt(oneHourAgo);
    
            utilities.sendRequest = function (parameters) {
                parameters.callback.onSuccess({ data: response.results });
            };
    
            vm.getLeaderboard(1);
    
            expect(vm.leaderboard[0].timeSpan).toBe('hour');
        });
    
        it('should set timeSpan to "hours" for 10 hours ago', function () {
            var tenHoursAgo = moment().subtract(10, 'hours').toDate();
            var response = leaderboardWithSubmissionAt(tenHoursAgo);
    
            utilities.sendRequest = function (parameters) {
                parameters.callback.onSuccess({ data: response.results });
            };
    
            vm.getLeaderboard(1);
    
            expect(vm.leaderboard[0].timeSpan).toBe('hours');
        });
    
        it('should set timeSpan to "minute" for 1 minute ago', function () {
            var oneMinuteAgo = moment().subtract(1, 'minutes').toDate();
            var response = leaderboardWithSubmissionAt(oneMinuteAgo);
    
            utilities.sendRequest = function (parameters) {
                parameters.callback.onSuccess({ data: response.results });
            };
    
            vm.getLeaderboard(1);
    
            expect(vm.leaderboard[0].timeSpan).toBe('minute');
        });
    
        it('should set timeSpan to "minutes" for 30 minutes ago', function () {
            var thirtyMinutesAgo = moment().subtract(30, 'minutes').toDate();
            var response = leaderboardWithSubmissionAt(thirtyMinutesAgo);
    
            utilities.sendRequest = function (parameters) {
                parameters.callback.onSuccess({ data: response.results });
            };
    
            vm.getLeaderboard(1);
    
            expect(vm.leaderboard[0].timeSpan).toBe('minutes');
        });
    
        it('should set timeSpan to "second" for 1 second ago', function () {
            var oneSecondAgo = moment().subtract(1, 'seconds').toDate();
            var response = leaderboardWithSubmissionAt(oneSecondAgo);
    
            utilities.sendRequest = function (parameters) {
                parameters.callback.onSuccess({ data: response.results });
            };
    
            vm.getLeaderboard(1);
    
            expect(vm.leaderboard[0].timeSpan).toBe('second');
        });
    
        it('should set timeSpan to "seconds" for 45 seconds ago', function () {
            var fortyFiveSecondsAgo = moment().subtract(45, 'seconds').toDate();
            var response = leaderboardWithSubmissionAt(fortyFiveSecondsAgo);
    
            utilities.sendRequest = function (parameters) {
                parameters.callback.onSuccess({ data: response.results });
            };
    
            vm.getLeaderboard(1);
    
            expect(vm.leaderboard[0].timeSpan).toBe('seconds');
        });
    });
});
