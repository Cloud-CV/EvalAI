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
});
