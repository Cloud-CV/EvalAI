(function () {
    'use strict';

    angular
        .module('evalai')
        .controller('CookieConsentController', CookieConsentController);

    CookieConsentController.$inject = ['$window', '$timeout'];

    function CookieConsentController($window, $timeout) {
        var vm = this;
        var COOKIE_KEY = 'cookie_consent';
        var storedValue = $window.localStorage.getItem(COOKIE_KEY);

        vm.cookieConsentResponded = storedValue === 'true' || storedValue === 'false';

        vm.acceptCookies = function () {
            $window.localStorage.setItem(COOKIE_KEY, 'true');
            $timeout(function () {
                vm.cookieConsentResponded = true;
            });
        };

        vm.declineCookies = function () {
            $window.localStorage.setItem(COOKIE_KEY, 'false');
            $timeout(function () {
                vm.cookieConsentResponded = true;
            });
        };
    }
})();
