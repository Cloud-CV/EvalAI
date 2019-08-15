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
});
