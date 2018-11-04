// Invoking IIFE for dashboard

(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('WebCtrl', WebCtrl);

    WebCtrl.$inject = ['utilities', '$state', '$stateParams', '$rootScope'];

    function WebCtrl(utilities, $rootScope) {
        var vm = this;

        vm.user = {};

        utilities.hideLoader();

        angular.element().find(".side-intro").addClass("z-depth-3");

        // get token
        var userKey = utilities.getData('userKey');
        if (userKey) {
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
                    }
                },
                onError: function(response) {
                    var details = response.data;
                    $rootScope.notify("error", details.error);
                }
            };

            utilities.sendRequest(parameters);
        }
    }

})();
