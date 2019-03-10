// Invoking IIFE
(function () {

    'use strict';

    angular
        .module('evalai')
        .controller('ChallengeInviteCtrl', ChallengeInviteCtrl);

    ChallengeInviteCtrl.$inject = ['utilities', 'loaderService', '$scope', '$rootScope', '$state', '$http', '$stateParams'];

    function ChallengeInviteCtrl(utilities, loaderService, $scope, $rootScope, $state, $http, $stateParams) {

        var vm = this;
        vm.invitationKey = $stateParams.invitationKey;

        vm.registerChallengeParticipant = function (registerChallengeParticipantForm) {
            if (registerChallengeParticipantForm) {
                var parameters = {};
                parameters.url = 'accounts/accept/invitation/' + vm.invitationKey + '/';
                parameters.method = 'PUT';
                parameters.token = null;
                parameters.data = {
                    "first_name": vm.first_name,
                    "last_name": vm.last_email,
                    "password": vm.password,
                };
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
        };

        var parameters = {};
        parameters.url = 'accounts/accept/invitation/' + vm.invitationKey + '/';
        parameters.method = 'GET';
        parameters.token = null;
        parameters.callback = {
            onSuccess: function (response) {
                vm.data = response.data;
                var status = response.status;
                if (status === 200) {
                    vm.challengeTitle = vm.data.challenge_title;
                    vm.host = vm.data.challenge_host_team_name;
                    vm.email = vm.data.email;
                    vm.username = vm.data.username;
                } else {
                    $state.go('error-404');
                }
            },
            onError: function (response) {
                vm.data = response.data;
                $state.go('error-404');
                $rootScope.notify('error', vm.data.error);
            }
        };
        utilities.sendRequest(parameters);
    }
})();
