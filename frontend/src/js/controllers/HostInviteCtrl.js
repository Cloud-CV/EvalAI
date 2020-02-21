// Invoking IIFE
(function () {

    'use strict';

    angular
        .module('evalai')
        .controller('HostInviteCtrl', HostInviteCtrl);

    HostInviteCtrl.$inject = ['utilities', 'loaderService', '$scope', '$rootScope', '$state', '$http', '$stateParams'];

    function HostInviteCtrl(utilities, loaderService, $scope, $rootScope, $state, $http, $stateParams) {

        var vm = this;
        vm.token = $stateParams.token;
        vm.pk = $stateParams.pk;

        var parameters = {};
        parameters.url = 'hosts/add_self_to_host_team/' + vm.pk + '/join/' + vm.token;
        parameters.method = 'POST';
        var userKey = utilities.getData('userKey');
        vm.authToken = userKey;
        if (userKey) {
            parameters.token = userKey;
        }
        parameters.callback = {
            onSuccess: function (response) {
                var status = response.status;
                if (status == 202) {
                    $state.go('web.teams');
                    $rootScope.notify("success", "You've successfully accepted the challenge invitation.");
                }
            },
            onError: function (response) {
                var error = response.error;
                $rootScope.notify("error", error);
                $state.go('web.dashboard');
            }
        };
        utilities.sendRequest(parameters);
    }
})();
