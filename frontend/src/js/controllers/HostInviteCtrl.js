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
        parameters.callback = {
            onSuccess: function (response) {
                var status = response.status;
                if (status == 200) {
                    $state.go('auth.login');
                    $rootScope.notify("success", "You've successfully accepted the challenge invitation.");
                }
            },
            onError: function (response) {
                var error = response.error;
                $rootScope.notify("error", error);
            }
        };
        utilities.sendRequest(parameters);
    }
})();
