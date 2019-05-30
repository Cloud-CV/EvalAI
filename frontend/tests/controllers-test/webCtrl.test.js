'use strict';

describe('Unit tests for web controller', function () {
    beforeEach(angular.mock.module('evalai'));

    var $controller, createController, $rootScope, $scope, utilities, $state, $stateParams, vm;

    beforeEach(inject(function (_$controller_, _$injector_, _$rootScope_, _utilities_, _$state_, _$stateParams_) {
        $controller = _$controller_;
        $rootScope = _$rootScope_;
        utilities = _utilities_;
        $state =_$state_;
        $stateParams = _$stateParams_;

        $scope = $rootScope.$new();
        createController = function () {
            return $controller('WebCtrl', {$scope: $scope});
        };
        vm = createController();
    }));

    describe('Global variables', function () {
        beforeEach(function () {
            spyOn(utilities, 'hideLoader');
            spyOn(utilities, 'getData');
        });

        it('has default values', function () {
            vm = createController();
            expect(vm.user).toEqual({});
            expect(utilities.hideLoader).toHaveBeenCalled();
            utilities.storeData('userKey', 'encrypted');
            expect(utilities.getData).toHaveBeenCalledWith('userKey');
        });
    });

    describe('Unit tests for global backend call `auth/user/`', function () {
        var success, successResponse, errorResponse;

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

        it('successfully get the user details', function () {
            success = true;
            successResponse = {
                username: "user",
                first_name: "firstname",
                last_name: "lastname"
            };
            vm = createController();
            expect(vm.name).toEqual(successResponse.username);
        });
    });
});
