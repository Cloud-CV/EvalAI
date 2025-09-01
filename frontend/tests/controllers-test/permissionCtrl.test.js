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
        utilities.storeData('emailError', 'Email is not verified');
        vm = $controller('PermCtrl', { $scope: $scope });
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

    describe('requestLink', function () {
        beforeEach(function () {
            spyOn(utilities, 'getData').and.returnValue('dummyUserKey');
            vm = createController();
        });

        it('should set sendMail true and notify success on success', function () {
            spyOn(utilities, 'sendRequest').and.callFake(function (params) {
                params.callback.onSuccess();
            });
            spyOn($rootScope, 'notify');
            vm.requestLink();
            expect(vm.sendMail).toBe(true);
            expect($rootScope.notify).toHaveBeenCalledWith('success', 'The verification link was sent again.');
        });

        it('should notify error with wait time on 429 error', function () {
            spyOn(utilities, 'sendRequest').and.callFake(function (params) {
                params.callback.onError({
                    status: 429,
                    data: { detail: 'Try again in 120 seconds.' }
                });
            });
            spyOn($rootScope, 'notify');
            vm.requestLink();
            expect($rootScope.notify).toHaveBeenCalledWith('error', 'Request limit exceeded. Please wait for 2 minutes and try again.');
        });

        it('should notify generic error on other errors', function () {
            spyOn(utilities, 'sendRequest').and.callFake(function (params) {
                params.callback.onError({
                    status: 400,
                    data: { detail: 'Error code 123' } // <-- contains a number
                });
            });
            spyOn($rootScope, 'notify');
            vm.requestLink();
            expect($rootScope.notify).toHaveBeenCalledWith('error', 'Something went wrong. Please try again.');
        });
    });
});
