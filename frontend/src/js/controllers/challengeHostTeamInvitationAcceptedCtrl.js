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
        
        // Controller properties
        vm.invitationKey = $stateParams.invitation_key;
        vm.invitationDetails = {};
        vm.isLoading = true;
        vm.isAccepting = false;
        vm.isLoggedIn = !!userKey;
        vm.error = null;
        vm.showLogoutOption = false;
        
        // Exposed functions
        vm.fetchInvitationDetails = fetchInvitationDetails;
        vm.acceptInvitation = acceptInvitation;
        vm.redirectToLogin = redirectToLogin;
        vm.logout = logout;
        
        // Initialize controller
        activate();
        function activate() {
            var storedInvitationKey = $window.sessionStorage.getItem('pendingInvitationKey');
            
            if (storedInvitationKey && !vm.invitationKey) {
                console.debug('Redirecting to invitation page with stored key');
                $state.go('web.challenge-host-team-invitation-accept', {invitation_key: storedInvitationKey});
                return;
            }
            
            if (vm.isLoggedIn) {
                console.debug('User is logged in, fetching invitation details');
                fetchInvitationDetails();
            } else {
                console.debug('User is not logged in, redirecting to login');
                vm.isLoading = false;
                redirectToLogin();
            }
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
            console.debug('Successfully fetched invitation details');
            vm.invitationDetails = response.data;
            vm.isLoading = false;
            
            if ($window.sessionStorage.getItem('pendingInvitationKey') === vm.invitationKey) {
                console.debug('Removing stored invitation key after successful fetch');
                $window.sessionStorage.removeItem('pendingInvitationKey');
            }
        }
        

        function handleFetchError(response) {
            vm.isLoading = false;
            console.error('Error fetching invitation details:', response);
            
            const errorConfig = {
                401: {
                    icon: 'warning',
                    title: 'Authentication Required',
                    message: 'You need to log in to view this invitation.',
                    status: 'warning',
                    timeout: 7000,
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
                    timeout: 10000,
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
                    timeout: 5000,
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
                    timeout: 8000,
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
            
            handleNotification({
                message: response.data.message || 'You have successfully joined the team!',
                title: 'Success',
                status: 'success',
                action: function() {
                    $window.sessionStorage.removeItem('pendingInvitationKey');
                    $state.go('web.challenge-host-teams');
                }
            });
        }
        
        /**
         * Handle errors when accepting invitation
         */
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
                console.debug('Storing invitation key before redirecting to login:', vm.invitationKey);
                $window.sessionStorage.setItem('pendingInvitationKey', vm.invitationKey);
            }
            
            $rootScope.previousState = 'web.challenge-host-team-invitation-accept';
            $rootScope.previousStateParams = { invitation_key: vm.invitationKey };
            
            // Redirect to login page
            $state.go('auth.login');
        }
        
        function logout() {
            if (vm.invitationKey) {
                console.debug('Storing invitation key before logout:', vm.invitationKey);
                $window.sessionStorage.setItem('pendingInvitationKey', vm.invitationKey);
            }
            
            utilities.deleteData('userKey');
            utilities.deleteData('refreshJWT');
            
            // Update logged in status
            vm.isLoggedIn = false;
            
            // Redirect to login
            $state.go('auth.login');
        }
        
        function handleError(options) {
            console.error(options.title || 'Error', options.message);
            
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
        
        function showToaster(type, title, message, timeout) {
            const icons = {
                success: 'check_circle_outline',
                warning: 'warning_amber',
                error:   'error_outline',
                info:    'info_outline'
            };
            const iconName = icons[type] || icons.info;
    
            toaster.pop({
                type: type,
                title: '',
                body: `
                  <div class="custom-toast ${type}-toast" style="display: flex; align-items: flex-start; padding: 10px;">
                    <div style="flex:1;">
                      <strong style="display:block; margin-bottom:4px; font-size:16px;">
                        ${title}
                      </strong>
                      <p style="margin:0; font-size:14px;">
                        ${message}
                      </p>
                    </div>
                  </div>
                `,
                bodyOutputType: 'trustedHtml',
                timeout: timeout || 5000,
                dismissButton: true,
                dismissible: true,
                positionClass: 'toast-top-right'
            });
        }
    }
})();
