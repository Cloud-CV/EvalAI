// Invoking IIFE

(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('MainCtrl', MainCtrl);

    MainCtrl.$inject = ['utilities', '$rootScope', '$state'];

    function MainCtrl(utilities, $rootScope, $state) {

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
                onError: function(error, status) {
                    if (status == 401) {
                        alert("")
                        utilities.resetStorage();
                        $state.go("auth.login");
                        $rootScope.isAuth = false;
                    }
                }
            };

            utilities.sendRequest(parameters);
        }

    }

})();
