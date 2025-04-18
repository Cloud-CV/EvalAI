'use strict';

describe('Unit tests for challenge invite controller', function () {
    beforeEach(angular.mock.module('evalai'));

    var $controller, createController, $rootScope, $state, $scope, utilities, vm;

    beforeEach(inject(function (_$controller_,  _$rootScope_, _$state_, _utilities_,) {
        $controller = _$controller_;
        $rootScope = _$rootScope_;
        $state = _$state_;
        utilities = _utilities_;

        $scope = $rootScope.$new();
        createController = function () {
            return $controller('ChallengeInviteCtrl', {$scope: $scope});
        };
        vm = $controller('ChallengeInviteCtrl', { $scope: $scope });
    }));

    describe('Unit tests for registerChallengeParticipant function \
    `challenges/<invitation_key>/accept-invitation/`', function () {
        var success;
        var errorResponse = 'error';

        beforeEach(function () {
            spyOn($rootScope, 'notify');
            spyOn($state, 'go');
            vm.first_name = "firstName";
            vm.last_name = "lastName";
            vm.password = "password";

            utilities.sendRequest = function (parameters) {
                if (success) {
                    parameters.callback.onSuccess({
                        status: 200
                    });
                } else {
                    parameters.callback.onError({
                        error: errorResponse
                    });
                }
            };
        });

        it('successfully accepted the challenge invitation', function () {
            success = true;
            vm.registerChallengeParticipant();
            expect($state.go).toHaveBeenCalledWith('auth.login');
            expect($rootScope.notify).toHaveBeenCalledWith("success", "You've successfully accepted the challenge invitation.");
        });

        it('backend error', function () {
            success = false;
            vm.registerChallengeParticipant();
            expect($rootScope.notify).toHaveBeenCalledWith("error", errorResponse);
        });
    });

    describe('Unit tests for global backend call', function () {
        var success, status;
        var successResponse = {
            challenge_title: "challenge title",
            challenge_host_team_name: "challenge host team name",
            email: "abc@gmail.com",
            user_details: "some details"
        };
        var errorResponse = {
            error: 'error'
        };

        beforeEach(function () {
            spyOn($rootScope, 'notify');
            spyOn($state, 'go');
            vm.first_name = "First Name";
            vm.last_name = "Last Name";
            vm.password = "Password";

            utilities.sendRequest = function (parameters) {
                if (success) {
                    parameters.callback.onSuccess({
                        data: successResponse,
                        status: status
                    });
                } else {
                    parameters.callback.onError({
                        data: errorResponse
                    });
                }
            };
        });

        it('successfully accept invitation `challenges/<invitation_key>/accept-invitation/`', function () {
            success = true;
            status = 200;
            vm = createController();
            expect(vm.data).toEqual(successResponse);
            expect(vm.challengeTitle).toEqual(successResponse.challenge_title);
            expect(vm.host).toEqual(successResponse.challenge_host_team_name);
            expect(vm.email).toEqual(successResponse.email);
            expect(vm.userDetails).toEqual(successResponse.user_details);
        });

        it('when status other than 200 `challenges/<invitation_key>/accept-invitation/`', function () {
            success = true;
            status = !200;
            vm = createController();
            expect(vm.data).toEqual(successResponse);
            expect($state.go).toHaveBeenCalledWith('error-404');
        });

        it('404 backend error `challenges/<invitation_key>/accept-invitation/`', function () {
            success = false;
            status = 404;
            vm = createController();
            expect(vm.data).toEqual(errorResponse);
            expect($state.go).toHaveBeenCalledWith('error-404');
            expect($rootScope.notify).toHaveBeenCalledWith('error', errorResponse.error);
        });
    });
});
