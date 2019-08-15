'use strict';

describe('Unit tests for submission files controller', function () {
    beforeEach(angular.mock.module('evalai'));

    var $controller, createController, $rootScope, $scope, utilities, $state, $stateParams, vm;

    beforeEach(inject(function (_$controller_, _$rootScope_, _utilities_, _$state_, _$stateParams_) {
        $controller = _$controller_;
        $rootScope = _$rootScope_;
        utilities = _utilities_;
        $state =_$state_;
        $stateParams = _$stateParams_;

        $scope = $rootScope.$new();
        createController = function () {
            return $controller('SubmissionFilesCtrl', {$scope: $scope});
        };
        vm = $controller('SubmissionFilesCtrl', { $scope: $scope });
    }));

    describe('Global variables', function () {
        it('has default values', function () {
            utilities.storeData('userKey', 'encrypted key');
            spyOn(utilities, 'getData');
            vm = createController();
            expect(utilities.getData).toHaveBeenCalledWith('userKey');
            expect(vm.bucket).toEqual($stateParams.bucket);
            expect(vm.key).toEqual($stateParams.key);
        });
    });

    describe('Unit tests for backend calls on load of controller', function () {
        var success, status;
        var errorResponse = {
            error: 'error'
        };
        var successResponse = {
            signed_url: "http://example.com"
        };

        beforeEach(function () {
            spyOn($rootScope, 'notify');
            spyOn($state, 'go');

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

        it('404 error on file submission `jobs/submission_files/?bucket=<bucket>&key=<key>`', function () {
            success = true;
            status = 404;
            vm = createController();
            expect($state.go).toHaveBeenCalledWith('error-404');
        });

        it('backend error `jobs/submission_files/?bucket=<bucket>&key=<key>`', function () {
            success = false;
            vm = createController();
            expect(vm.data).toEqual(errorResponse);
            expect($rootScope.notify).toHaveBeenCalledWith('error', errorResponse.error);
        });
    });
});
