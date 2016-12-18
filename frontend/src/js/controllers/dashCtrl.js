// Invoking IIFE for dashboard

(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('DashCtrl', DashCtrl);

    DashCtrl.$inject = ['utilities', '$state', '$rootScope'];

    function DashCtrl(utilities, $state, $rootScope) {
        var vm = this;

        // get token
        var userKey = utilities.getData('userKey');

        var parameters = {};
        parameters.url = 'auth/user/';
        parameters.method = 'GET';
        parameters.token = userKey;
        parameters.callback = {
            onSuccess: function(response, status) {
                if (status == 200) {
                    vm.name = response.username;
                }
            },
            onError: function(error, status) {
                if (status == 401) {
                    $rootScope.logout();
                } else {
                    vm.error = error;

                    // navigate to permissions denied page
                    $state.go('web.permission-denied');
                }



            }
        };

        utilities.sendRequest(parameters);
    }

})();
