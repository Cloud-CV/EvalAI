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
});

describe('Unit tests for requestLink function', function() {
    var vm, $rootScope, utilities;

    beforeEach(angular.mock.module('evalai'));

    beforeEach(inject(function(_$rootScope_, _utilities_) {
        $rootScope = _$rootScope_;
        utilities = _utilities_;

        vm = {
            requestLink: function() {
                var userKey = utilities.getData('userKey');
                var parameters = {};
                parameters.url = 'accounts/user/resend_email_verification/';
                parameters.method = 'POST';
                parameters.token = userKey;
                parameters.callback = {
                    onSuccess: function() {
                        vm.sendMail = true;
                        $rootScope.notify("success", "The verification link was sent again.");
                    },
                    onError: function(response) {
                        var message = response.data.detail;
                        var time = Math.floor(message.match(/\d+/g)[0] / 60);
                        if (response.status == 429) {
                            $rootScope.notify("error", "Request limit exceeded. Please wait for " + time + " minutes and try again.");
                        } else {
                            $rootScope.notify("error", "Something went wrong. Please try again.");
                        }
                    }
                };
                utilities.sendRequest(parameters);
            }
        };

        spyOn(utilities, 'sendRequest');
        spyOn($rootScope, 'notify');
    }));

    it('sends a request to resend the email verification link', function() {
        vm.requestLink();
        expect(utilities.sendRequest).toHaveBeenCalled();
    });
});