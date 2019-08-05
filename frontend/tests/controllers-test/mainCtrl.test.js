'use strict';

describe('Unit tests for main controller', function () {
    beforeEach(angular.mock.module('evalai'));

    var $controller, createController, $rootScope, $scope, utilities, $state, vm;

    beforeEach(inject(function (_$controller_, _$rootScope_, _$state_, _utilities_,) {
        $controller = _$controller_;
        $rootScope = _$rootScope_;
        utilities = _utilities_;
        $state = _$state_;

        $scope = $rootScope.$new();
        createController = function () {
            return $controller('MainCtrl', {$scope: $scope});
        };
        vm = $controller('MainCtrl', { $scope: $scope });
    }));

    describe('Global variables', function () {
        it('has default values', function () {
            vm = createController();
            expect(vm.user).toEqual({});
            expect(vm.challengeList).toEqual([]);
            expect(vm.isChallenge).toBeTruthy({});
            expect(vm.redirectUrl).toEqual({});
        });
    });

    describe('Unit tests for getChallenge function `challenges/featured/`', function () {
        var success, successResponse;
        var errorResponse = 'error';

        beforeEach(function () {
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

        it('successfully get featured challenge', function () {
            success = true;
            successResponse = 'success';
            vm.getChallenge();
            expect(vm.challengeList).toEqual(successResponse);
        });
    });

    describe('Unit tests for init function `auth/user/`', function () {
        var success, successResponse, errorResponse;

        beforeEach(function () {
            spyOn($state, 'go');
            spyOn(utilities, 'resetStorage');
            utilities.storeData('userKey', 'encrypted key');

            utilities.sendRequest = function (parameters) {
                if (success) {
                    parameters.callback.onSuccess({
                        data: successResponse,
                        status: 200
                    });
                } else {
                    parameters.callback.onError({
                        data: errorResponse,
                        status: 401
                    });
                }
            };
        });

        it('check for the authenticated user', function () {
            success = true;
            successResponse = {
                username: 'abc123'
            };
            vm.init();
            expect(utilities.resetStorage).not.toHaveBeenCalled();
            expect(vm.user.name).toEqual(successResponse.username);
        });

        it('init function backend error', function () {
            success = false;
            errorResponse = 'error';     
            vm.init();
            expect(utilities.resetStorage).toHaveBeenCalled();
            expect($state.go).toHaveBeenCalledWith("auth.login");
            expect($rootScope.isAuth).toBeFalsy();
        });
    });

    describe('Unit tests for hostChallenge function', function () {
        beforeEach(function () {
            spyOn($state, 'go');
        });

        it('redirect to challenge host teams tab if authenticated', function () {
            $rootScope.isAuth = true;
            vm.hostChallenge();
            expect($state.go).toHaveBeenCalledWith('web.challenge-host-teams');
        });

        it('redirect to login page', function () {
            $rootScope.isAuth = false;
            vm.hostChallenge();
            expect($state.go).toHaveBeenCalledWith('auth.login');
            expect($rootScope.previousState).toEqual("web.challenge-host-teams");
        });
    });

    describe('Unit tests for profileDropdown function', function () {
        var element = angular.element(".dropdown-button");

        it('mocking dropdown function on `angular.element`', function () {
            var dropdown = jasmine.createSpy();

            vm.profileDropdown();
            element = jasmine.createSpy().and.returnValue({
                dropdown: dropdown
            });
        });
    });
});
