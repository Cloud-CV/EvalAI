(function () {
    'use strict';

    angular
        .module('evalai')
        .controller('challengeHostTeamInvitationAcceptCtrl', challengeHostTeamInvitationAcceptCtrl);

    challengeHostTeamInvitationAcceptCtrl.$inject = [
        '$state', 
        '$stateParams', 
        'utilities', 
        'toaster', 
        'loaderService', 
        '$location', 
        '$rootScope',
        '$window',
        '$timeout'
    ];

    function challengeHostTeamInvitationAcceptCtrl($state, $stateParams, utilities, toaster, loaderService, $location, $rootScope, $window, $timeout) {
        var vm = this;
        var userKey = utilities.getData('userKey');
        vm.invitationKey = $stateParams.invitation_key;
        $window.sessionStorage.setItem('pendingInvitationKey',vm.invitationKey);
        vm.invitationDetails = {};
        vm.isLoading = true;
        vm.isAccepting = false;
        vm.isLoggedIn = !!userKey;
        vm.error = null;
        vm.showLogoutOption = false;
    
        vm.fetchInvitationDetails = fetchInvitationDetails;
        vm.acceptInvitation = acceptInvitation;
        vm.redirectToLogin = redirectToLogin;
        vm.logout = logout;
        
        // Initialize controller
        activate();
        function activate() {
            if (!vm.isLoggedIn) {
              vm.isLoading = false;
              return redirectToLogin();
            }
            var redirectAfterLogin = $window.sessionStorage.getItem('redirectAfterLogin');
            if (vm.isLoggedIn && redirectAfterLogin === 'web.challenge-host-team-invitation-accept') {
              return handleLoginSuccess();
            }
          
            var storedInvitationKey = $window.sessionStorage.getItem('pendingInvitationKey');
            if (!vm.invitationKey && storedInvitationKey) {
              vm.invitationKey = storedInvitationKey;
              return $state.go(
                'web.challenge-host-team-invitation-accept',
                { invitation_key: storedInvitationKey },
                { location: 'replace', notify: false }
              );
            }
          
            if (vm.invitationKey) {
              return fetchInvitationDetails();
            }
          
            handleError({
              message: 'Please click on invitation link sent to your mail again!',
              title: 'Click on Invitation',
              status: 'error'
            });
            vm.isLoading = false;
          }
          
        
        function fetchInvitationDetails() {
            if (!vm.invitationKey) {
                handleError({
                    message: 'Please click on invitation link sent to your mail again!',
                    title: 'Click on Invitation',
                    status: 'error'
                });
                vm.isLoading = false;
                return;
            }
            
            vm.isLoading = true;
            vm.error = null;
            
            var parameters = {
                url: 'hosts/team-invitation/' + vm.invitationKey + '/',
                method: 'GET',
                token: userKey,
                callback: {
                    onSuccess: handleFetchSuccess,
                    onError: handleFetchError
                }
            };
            
            utilities.sendRequest(parameters);
        }
        
        function handleFetchSuccess(response) {
            vm.invitationDetails = response.data;
            vm.isLoading = false;
        }
        
        function handleFetchError(response) {
            vm.isLoading = false;
            
            const errorConfig = {
                401: {
                    icon: 'warning',
                    title: 'Authentication Required',
                    message: 'You need to log in to view this invitation.',
                    status: 'warning',
                    timeout: 3000,
                    dismissButton: true,
                    action: () => {
                        vm.isLoggedIn = false;
                        redirectToLogin();
                    }
                },
                403: {
                    icon: 'error',
                    title: 'Wrong Account',
                    message: 'This invitation was sent to a different email address. Please log in with the correct account.',
                    status: 'error',
                    timeout: 3000,
                    dismissButton: true,
                    action: () => {
                        vm.showLogoutOption = true;
                    }
                },
                404: {
                    icon: 'error',
                    title: 'Invalid Invitation',
                    message: 'This invitation is invalid or has expired.',
                    status: 'error',
                    timeout: 3000,
                    dismissButton: true,
                    action: () => {
                        $timeout(() => $state.go('home'), 3000);
                    }
                },
                default: {
                    icon: 'error',
                    title: 'Error',
                    message: response.data.error || 'An error occurred while fetching the invitation details.',
                    status: 'error',
                    timeout: 3000,
                    dismissButton: true
                }
            };

            const config = errorConfig[response.status] || errorConfig.default;
            
            vm.error = config.message;
            
            displayErrorNotification(config);
            
            if (config.action) {
                config.action();
            }
        }

         //Display a styled error notification
         function displayErrorNotification(config) {
            toaster.pop({
              type:         config.status,
              title:        null,               
              toastClass:   'custom-toast',     
              bodyOutputType:'trustedHtml',
              body: `
                <div style="padding:10px;">
                  <strong style="display:block; font-size:16px;">
                    ${config.title}
                  </strong>
                  <p style="margin:4px 0 0; font-size:14px;">
                    ${config.message}
                  </p>
                  ${config.helpText ? `
                    <p style="margin:8px 0 0; font-size:12px;">
                      ${config.helpText}
                    </p>` : ''}
                </div>`,
              timeout:      config.timeout || 5000,
              dismissButton: config.dismissButton !== false,
              dismissible:  true,
              positionClass:'toast-top-right'
            });
          }
          
          function showToaster(type, title, message, timeout) {
            toaster.pop({
              type:         type,
              title:        null,
              toastClass:   'custom-toast',
              bodyOutputType:'trustedHtml',
              body: `
                <div style="padding:10px;">
                  <strong style="display:block; font-size:16px;">
                    ${title}
                  </strong>
                  <p style="margin:4px 0 0; font-size:14px;">
                    ${message}
                  </p>
                </div>`,
              timeout:      timeout || 5000,
              dismissButton:true,
              dismissible:  true,
              positionClass:'toast-top-right'
            });
          }

        function acceptInvitation() {
            if (!vm.isLoggedIn) {
                redirectToLogin();
                return;
            }
            
            vm.isAccepting = true;
            loaderService.startLoader('Accepting invitation...');
            
            var parameters = {
                url: 'hosts/team-invitation/' + vm.invitationKey + '/',
                method: 'POST',
                token: userKey,
                callback: {
                    onSuccess: handleAcceptSuccess,
                    onError: handleAcceptError
                }
            };
            
            utilities.sendRequest(parameters);
        }
        
        function handleAcceptSuccess(response) {
            vm.isAccepting = false;
            loaderService.stopLoader();
            
            // Only remove the pending invitation key after successful acceptance
            $window.sessionStorage.removeItem('pendingInvitationKey');
            
            handleNotification({
                message: response.data.message || 'You have successfully joined the team!',
                title: 'Success',
                status: 'success',
                action: function() {
                    $state.go('web.challenge-host-teams');
                }
            });
        }
        
        //Handle errors when accepting invitation
        function handleAcceptError(response) {
            vm.isAccepting = false;
            loaderService.stopLoader();
            
            if (response.status === 401) {
                handleError({
                    message: 'Your session has expired. Please log in again.',
                    title: 'Authentication Error',
                    status: 'error',
                    action: function() {
                        vm.isLoggedIn = false;
                        redirectToLogin();
                    }
                });
            } else {
                handleError({
                    message: response.data.error || 'An error occurred while accepting the invitation.',
                    title: 'Error',
                    status: 'error'
                });
            }
        }
        
        function redirectToLogin() {
          if (vm.invitationKey) {
              // Store both the invitation key and the desired redirect state
              $window.sessionStorage.setItem('pendingInvitationKey', vm.invitationKey);
              $window.sessionStorage.setItem('redirectAfterLogin', 'web.challenge-host-team-invitation-accept');
              
              // Pass invitation_key in URL params to keep it visible
              return $state.go('auth.login', {
                  invitation_key: vm.invitationKey,
                  redirect: 'invitation-accept'
              });
          }
      }
      

        function handleLoginSuccess() {
            var pendingInvitationKey = $window.sessionStorage.getItem('pendingInvitationKey');
            var redirectAfterLogin = $window.sessionStorage.getItem('redirectAfterLogin');
            
            if (pendingInvitationKey && redirectAfterLogin === 'web.challenge-host-team-invitation-accept') {
              // Don't remove pendingInvitationKey yet, the accept page needs it
              $window.sessionStorage.removeItem('redirectAfterLogin');
              return $state.go('web.challenge-host-team-invitation-accept', {
                invitation_key: pendingInvitationKey
              });
            }
            
            // Default redirect if no pending invitation
            return $state.go('home');
          }

        
          function logout() {
            if (vm.invitationKey) {
              $window.sessionStorage.setItem('pendingInvitationKey', vm.invitationKey);
              $window.sessionStorage.setItem('redirectAfterLogin', 'web.challenge-host-team-invitation-accept');
            }
            
            utilities.deleteData('userKey');
            utilities.deleteData('refreshJWT');
            
            $state.go('auth.login', {
              invitation_key: vm.invitationKey,
              redirect: 'invitation-accept'
            });
          }
        
        function handleError(options) {
            
            vm.error = options.message;
            showToaster(options.status || 'error', options.title || 'Error', options.message);
            
            if (typeof options.action === 'function') {
                options.action();
            }
        }
        
        function handleNotification(options) {
            showToaster(options.status || 'success', options.title || 'Notification', options.message);
            
            // Execute any additional actions
            if (typeof options.action === 'function') {
                options.action();
            }
        }
    }
})();
