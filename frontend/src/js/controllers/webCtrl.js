// Invoking IIFE for dashboard

(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('WebCtrl', WebCtrl);

    WebCtrl.$inject = ['utilities', '$state', '$stateParams', '$rootScope'];

    function WebCtrl(utilities, $state, $stateParams, $rootScope) {
        var vm = this;

        vm.user = {};

        utilities.hideLoader();

        angular.element().find(".side-intro").addClass("z-depth-3");

        // get token
        var userKey = utilities.getData('userKey');

        var parameters = {};
        parameters.url = 'auth/user/';
        parameters.method = 'GET';
        parameters.token = userKey;
        parameters.callback = {
            onSuccess: function(response) {
                var status = response.status;
                var result = response.data;
                if (status == 200) {
                    vm.name = result.username;
                    vm.email = result.email;
                    utilities.storeData('name', vm.name);
                    utilities.storeData('email',vm.email);

                }
            },
            onError: function() {
                $rootScope.notify("error", "Some error have occured , please try again !");
            }
        };

        utilities.sendRequest(parameters);
    }

})();
