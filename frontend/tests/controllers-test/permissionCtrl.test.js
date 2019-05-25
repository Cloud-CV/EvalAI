'use strict';

describe('Unit tests for permission controller', function () {
    beforeEach(angular.mock.module('evalai'));

    var $controller, createController, $rootScope, $scope, utilities, vm;

    beforeEach(inject(function (_$controller_, _$rootScope_, _utilities_,) {
        $controller = _$controller_;
        $rootScope = _$rootScope_;
        utilities = _utilities_;

        $scope = $rootScope.$new();
        createController = function () {
            return $controller('PermCtrl', {$scope: $scope});
        };
    }));

    describe('Global variables', function () {
        beforeEach(function () {
            spyOn(utilities, 'getData');
        });

        it('permission controller has default values', function () {
            vm = createController();
            expect(utilities.getData).toHaveBeenCalledWith('emailError');
            expect(vm.emailError).toEqual(utilities.getData('emailError'));
        });
    });
});
