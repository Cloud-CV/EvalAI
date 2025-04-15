'use strict';

describe('Unit tests for CookieConsentController', function () {
    beforeEach(angular.mock.module('evalai'));

    var $controller, $rootScope, $scope, $timeout, $window, $httpBackend, createController;
    var fakeStorage;

    beforeEach(inject(function (_$controller_, _$rootScope_, _$timeout_, _$window_, _$httpBackend_) {
        $controller = _$controller_;
        $rootScope = _$rootScope_;
        $timeout = _$timeout_;
        $window = _$window_;
        $httpBackend = _$httpBackend_;

        $scope = $rootScope.$new();
        fakeStorage = {};

        $httpBackend.whenGET(/.*/).respond(200);

        spyOn($window.localStorage, 'getItem').and.callFake(function (key) {
            return fakeStorage[key] || null;
        });

        spyOn($window.localStorage, 'setItem').and.callFake(function (key, value) {
            fakeStorage[key] = value;
        });

        createController = function () {
            return $controller('CookieConsentController', {
                $window: $window,
                $timeout: $timeout
            });
        };
    }));

    it('should set vm.cookieConsentResponded to false if no cookie preference is set', function () {
        delete fakeStorage['cookie_consent'];
        var vm = createController();
        expect(vm.cookieConsentResponded).toBe(false);
    });

    it('should set vm.cookieConsentResponded to true if stored value is "true"', function () {
        fakeStorage['cookie_consent'] = 'true';
        var vm = createController();
        expect(vm.cookieConsentResponded).toBe(true);
    });

    it('should set vm.cookieConsentResponded to true if stored value is "false"', function () {
        fakeStorage['cookie_consent'] = 'false';
        var vm = createController();
        expect(vm.cookieConsentResponded).toBe(true);
    });

    it('should store "true" on acceptCookies and set vm.cookieConsentResponded to true', function () {
        var vm = createController();
        vm.acceptCookies();
        $timeout.flush();
        expect(fakeStorage['cookie_consent']).toBe('true');
        expect(vm.cookieConsentResponded).toBe(true);
    });

    it('should store "false" on declineCookies and set vm.cookieConsentResponded to true', function () {
        var vm = createController();
        vm.declineCookies();
        $timeout.flush();
        expect(fakeStorage['cookie_consent']).toBe('false');
        expect(vm.cookieConsentResponded).toBe(true);
    });
});
