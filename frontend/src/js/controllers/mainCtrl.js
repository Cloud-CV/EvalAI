// Invoking IIFE

(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('MainCtrl', MainCtrl);

    MainCtrl.$inject = ['utilities', '$rootScope'];

    function MainCtrl(utilities, $rootScope) {

        var vm = this;

        vm.user = {};

        // get token
        var userKey = utilities.getData('userKey');

        if (userKey) {
            var parameters = {};
            parameters.url = 'auth/user/';
            parameters.method = 'GET';
            parameters.token = userKey;
            parameters.callback = {
                onSuccess: function(response, status) {
                    if (status == 200) {
                        vm.user.name = response.username;
                    }
                },
                onError: function() {
                    if (status == 401) {
                        $rootScope.logout();
                    }
                }
            };

            utilities.sendRequest(parameters);
        }

    }

})();
