// Invoking IIFE for dashboard
(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('DashCtrl', DashCtrl);

    DashCtrl.$inject = ['utilities', '$state', '$rootScope', '$mdDialog'];

    function DashCtrl(utilities, $state, $rootScope, $mdDialog) {
        var vm = this;

        // get token
        var userKey = utilities.getData('userKey');

        var parameters = {};
        parameters.url = 'auth/user/';
        parameters.method = 'GET';
        parameters.token = userKey;
        parameters.callback = {
            onSuccess: function(response) {
                var status = response.status;
                var details = response.data;
                if (status == 200) {
                    vm.name = details.username;
                }
            },
            onError: function(response) {
                var status = response.status;
                var error = response.data;
                if (status == 403) {
                    vm.error = error;

                    // navigate to permissions denied page
                    $state.go('web.permission-denied');
                } else if (status == 401) {
                    alert("Timeout, Please login again to continue!");
                    utilities.resetStorage();
                    $state.go("auth.login");
                    $rootScope.isAuth = false;

                }
            }
        };

        utilities.sendRequest(parameters);

        vm.hostChallenge = function() {

            var alert = $mdDialog.alert()
                .title('Host a challenge')
                .htmlContent('Please send an email to <a href="mailto:admin@cloudcv.org" class="blue-text">admin@cloudcv.org</a> with the details of the challenge and we will get back soon.')
                .ok('Close');

            $mdDialog.show(alert);
        };
    }

})();
