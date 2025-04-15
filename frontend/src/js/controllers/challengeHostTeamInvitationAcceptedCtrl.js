'use strict';

angular.module('evalai')
  .controller('ChallengeHostTeamInvitationAcceptCtrl', ['$scope', '$state', '$stateParams', 'utilities', 'ApiFactory', 'loaderService',
    function ($state, $stateParams, utilities, ApiFactory, loaderService) {
      var vm = this;
      
      vm.invitationKey = $stateParams.invitation_key;
      vm.isProcessing = false;
      vm.error = null;
      
      var parameters = {};
      parameters.url = 'hosts/accept-invitation/' + vm.invitationKey + '/';
      parameters.method = 'GET';
      parameters.token = utilities.getData('token');
      
      loaderService.startLoader('Loading invitation details...');
      
      ApiFactory.getApiData(parameters)
        .then(function(response) {
          vm.teamName = response.data.team_name;
          vm.invitedBy = response.data.invited_by;
          vm.email = response.data.email;
          loaderService.stopLoader();
        })
        .catch(function(response) {
          vm.error = response.data.error || 'An error occurred while loading the invitation.';
          loaderService.stopLoader();
        });
      
      vm.acceptInvitation = function() {
        vm.isProcessing = true;
        
        var parameters = {};
        parameters.url = 'hosts/accept-invitation/' + vm.invitationKey + '/';
        parameters.method = 'POST';
        parameters.token = utilities.getData('token');
        
        ApiFactory.sendRequest(parameters)
          .then(function() {
            vm.isProcessing = false;
            utilities.showMessage('success', 'You have successfully joined the team!');
            $state.go('challenge-host-teams');
          })
          .catch(function(response) {
            vm.isProcessing = false;
            vm.error = response.data.error || 'An error occurred while accepting the invitation.';
          });
      };
    }
  ]);
