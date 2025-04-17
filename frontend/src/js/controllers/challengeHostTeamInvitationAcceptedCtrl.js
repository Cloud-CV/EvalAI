'use strict';

angular.module('evalai')
  .controller('ChallengeHostTeamInvitationAcceptCtrl', [
    '$scope', '$state', '$stateParams', 'utilities', 'ApiFactory', 'loaderService',
    function ($scope, $state, $stateParams, utilities, ApiFactory, loaderService) {
      var vm = this;

      // 1) grab the key from the URL
      vm.invitationKey = $stateParams.invitation_key;
      vm.isProcessing   = false;
      vm.error          = null;

      // 2) build the GET parameters for the "invitation redirect" API
      var getParams = {
        url:    'hosts/invitation/' + vm.invitationKey + '/',  // ← new redirect URL
        method: 'GET',
        token:  utilities.getData('token')
      };

      // 3) load the invitation details (or detect that login is needed)
      loaderService.startLoader('Loading invitation details...');
      ApiFactory.getApiData(getParams)
        .then(function(response) {
          // already logged in → show the details
          vm.teamName  = response.data.team_name;
          vm.invitedBy = response.data.invited_by;
          vm.email     = response.data.email;
          loaderService.stopLoader();
        })
        .catch(function(response) {
          loaderService.stopLoader();

          // not logged in → backend told us to login first
          if (response.status === 401 && response.data.login_required) {
            // save the key for use after login
            sessionStorage.setItem('pendingInvitationKey', vm.invitationKey);
            // send them to the login page
            $state.go('auth.login');
          } else {
            // some other error (invalid/expired link, etc.)
            vm.error = response.data.error ||
                       'An error occurred while loading the invitation.';
          }
        });

      // 4) when they click “Accept”, call the protected accept API
      vm.acceptInvitation = function() {
        vm.isProcessing = true;

        var postParams = {
          url:    'hosts/accept-invitation/' + vm.invitationKey + '/',
          method: 'POST',
          token:  utilities.getData('token')
        };

        ApiFactory.sendRequest(postParams)
          .then(function() {
            vm.isProcessing = false;
            utilities.showMessage('success',
              'You have successfully joined the team!'
            );
            $state.go('challenge-host-teams');
          })
          .catch(function(response) {
            vm.isProcessing = false;

            // If somehow they got logged out between GET and POST:
            if (response.status === 401 && response.data.login_required) {
              sessionStorage.setItem('pendingInvitationKey', vm.invitationKey);
              $state.go('auth.login');
            } else {
              vm.error = response.data.error ||
                         'An error occurred while accepting the invitation.';
            }
          });
      };
    }
  ]);
