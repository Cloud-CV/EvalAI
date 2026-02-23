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

describe('PermCtrl', function() {
    beforeEach(angular.mock.module('evalai'));
    var utilities, $rootScope, vm;
    var mockUserKey = 'User key'; //adding this to mock userkey

    beforeEach(inject(function(_utilities_, _$rootScope_, $controller) {
        utilities = _utilities_;
        $rootScope = _$rootScope_;

        spyOn(utilities, 'getData').and.callFake(function(key) {
            if (key === 'emailError') {
                return 'Email error message';
            } else if (key === 'userKey') {
                return mockUserKey;
            }
        });

        spyOn(utilities, 'sendRequest').and.callFake(function() {});
        spyOn($rootScope, 'notify');
        vm = $controller('PermCtrl', { utilities: utilities, $rootScope: $rootScope });
    }));

    it('should initialize with correct default values', function() {
        expect(utilities.getData).toHaveBeenCalledWith('emailError');
        expect(vm.emailError).toEqual('Email error message');
    });

    it('should call utilities.sendRequest with correct parameters when requestLink is called', function() {
        vm.requestLink();

        var expectedParameters = {
            url: 'accounts/user/resend_email_verification/',
            method: 'POST',
            token: mockUserKey,
            callback: jasmine.any(Object)
        };

        expect(utilities.sendRequest).toHaveBeenCalledWith(expectedParameters);
    });

    it('should notify success on successful request', function() {
        vm.requestLink();
        var successCallback = utilities.sendRequest.calls.mostRecent().args[0].callback.onSuccess;
        successCallback();
        expect(vm.sendMail).toBe(true);
        expect($rootScope.notify).toHaveBeenCalledWith('success', 'The verification link was sent again.');
    });

    it('should notify error when request limit is exceeded', function() {
        vm.requestLink();
        var errorCallback = utilities.sendRequest.calls.mostRecent().args[0].callback.onError;
        var response = {
            status: 429,
            data: {
                detail: "Request limit exceeded. Please wait for 30 minutes."
            }
        };
        errorCallback(response);

        var message = response.data.detail;
        var time = Math.floor(message.match(/\d+/g)[0] / 60);
        expect($rootScope.notify).toHaveBeenCalledWith('error', 'Request limit exceeded. Please wait for ' + time + ' minutes and try again.');
    });
});
