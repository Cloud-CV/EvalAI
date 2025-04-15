(function() {
    'use strict';

    angular
        .module('evalai')
        .controller('ChallengeHostInvitationAcceptCtrl', challengeHostInvitationAcceptCtrl);

    challengeHostInvitationAcceptCtrl.$inject = ['utilities', '$scope', '$state', '$stateParams', '$rootScope'];

    function challengeHostInvitationAcceptCtrl(utilities, $scope, $state, $stateParams, $rootScope) {
        var vm = this;
        var userKey = utilities.getData('userKey');
        vm.invitationKey = $stateParams.invitationKey;
        vm.isProcessing = true;
        
        // Process the invitation when the controller loads
        var parameters = {};
        parameters.url = 'hosts/accept-invitation/' + vm.invitationKey + '/';
        parameters.method = 'GET';
        parameters.token = userKey;
        parameters.callback = {
            onSuccess: function(response) {
                vm.isProcessing = false;
                vm.message = response.data.message;
                $rootScope.notify("success", vm.message);
                // Redirect to teams page after a delay
                setTimeout(function() {
                    $state.go('web.challenge-host-teams');
                }, 3000);
            },
            onError: function(response) {
                vm.isProcessing = false;
                vm.error = response.data.error || "There was an error processing your invitation.";
                $rootScope.notify("error", vm.error);
            }
        };
        utilities.sendRequest(parameters);
    }
})();
