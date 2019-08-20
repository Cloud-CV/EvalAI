'use strict';

describe('Unit tests for OurTeam Controller', function () {
    beforeEach(angular.mock.module('evalai'));

    var $controller, createController, $rootScope, $scope, utilities, vm;

    beforeEach(inject(function (_$controller_, _$rootScope_, _utilities_,) {
        $controller = _$controller_;
        $rootScope = _$rootScope_;
        utilities = _utilities_;

        $scope = $rootScope.$new();
        createController = function () {
            return $controller('ourTeamCtrl', {$scope: $scope});
        };
        vm = $controller('ourTeamCtrl', { $scope: $scope });
    }));

    describe('Unit tests for global backend call for listing the team `web/team/`', function () {
        var success, successResponse, errorResponse;
        var teamDetails = [
            {
                team_type: "Core Team",
                name: "xyz",
                email: "xyz@gmail.com",
                description: "some description",
            },
            {
                team_type: "Contributor",
                name: "abc",
                email: "abc@gmail.com",
                description: "some other description",
            }
        ];

        beforeEach(function () {
            utilities.sendRequest = function (parameters) {
                if (success) {
                    parameters.callback.onSuccess({
                        data: successResponse,
                        status: 200
                    });
                } else {
                    parameters.callback.onError({
                        data: errorResponse
                    });
                }
            };
        });

        teamDetails.forEach(member => {
            it('when `team_type` is ' + member.team_type, function () {
                successResponse = teamDetails;
                success = true;
                vm = createController();
                var coreTeamList = [];
                var contributingTeamList = [];
                if (member.team_type == "Core Team") {
                    expect(vm.coreTeamType).toEqual(member.team_type);
                    expect(vm.coreTeamList).toEqual(coreTeamList.push(member));
                } else {
                    expect(vm.contributingTeamType).toEqual(member.team_type);
                    expect(vm.contributingTeamList).toEqual(contributingTeamList.push(member));
                }
            });
        });

        it('when no team to display', function () {
            successResponse = [];
            success = true;
            vm = createController();
            expect(vm.noTeamDisplay).toEqual("Team will be updated very soon !");
        });
    });
});
