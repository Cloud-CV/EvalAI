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
        
        /**
         * Initialize the controller and handle pending invitations
         */
        function activate() {
            // Check for pending invitation from previous login attempt
            var storedInvitationKey = $window.sessionStorage.getItem('pendingInvitationKey');
            
            // Log for debugging
            console.debug('Activation - URL token:', vm.invitationKey);
            console.debug('Activation - Stored token:', storedInvitationKey);
            console.debug('Activation - Is logged in:', vm.isLoggedIn);
            
            // If we have a stored key but no key in URL, redirect with the proper key
            if (storedInvitationKey && !vm.invitationKey) {
                console.debug('Redirecting to invitation page with stored key');
                // Don't remove the key until we're sure the redirection worked
                $state.go('web.challenge-host-team-invitation-accept', {invitation_key: storedInvitationKey});
                return;
            }
            
            // Handle the invitation based on login status
            if (vm.isLoggedIn) {
                console.debug('User is logged in, fetching invitation details');
                // Delay removal of stored key until after successful API response
                fetchInvitationDetails();
            } else {
                console.debug('User is not logged in, redirecting to login');
                vm.isLoading = false;
                redirectToLogin();
            }
        }
        
        /**
         * Fetch invitation details from the API
         */
        function fetchInvitationDetails() {
            if (!vm.invitationKey) {
                vm.error = 'Invalid invitation link. No invitation key provided.';
                vm.isLoading = false;
                showToaster('error', 'Invalid Invitation', vm.error);
                console.error('No invitation key provided');
                return;
            }
            
            vm.isLoading = true;
            vm.error = null;
            
            console.debug('Fetching invitation details for key:', vm.invitationKey);
            
            var parameters = {
                url: 'hosts/team-invitation/' + vm.invitationKey+'/',
                method: 'GET',
                token: userKey,
                callback: {
                    onSuccess: handleFetchSuccess,
                    onError: handleFetchError
                }
            };
            
            utilities.sendRequest(parameters);
        }
        
        /**
         * Handle successful invitation details fetch
         */
        function handleFetchSuccess(response) {
            console.debug('Successfully fetched invitation details:', response.data);
            vm.invitationDetails = response.data;
            vm.isLoading = false;
            
            // Clear stored invitation key if it matches current key
            if ($window.sessionStorage.getItem('pendingInvitationKey') === vm.invitationKey) {
                console.debug('Removing stored invitation key after successful fetch');
                $window.sessionStorage.removeItem('pendingInvitationKey');
            }
        }
        
        /**
         * Handle errors when fetching invitation details
         */
        function handleFetchError(response) {
            vm.isLoading = false;
            console.error('Error fetching invitation details:', response);
            
            switch (response.status) {
                case 401:
                    // User needs to log in
                    console.debug('User unauthorized, redirecting to login');
                    vm.isLoggedIn = false;
                    redirectToLogin();
                    break;
                    
                case 403:
                    // Wrong user logged in
                    console.debug('Wrong user logged in, showing logout option');
                    vm.error = 'This invitation was sent to a different email address. Please log in with the correct account.';
                    showToaster('error', 'Wrong Account', vm.error);
                    vm.showLogoutOption = true;
                    break;
                    
                case 404:
                    // Invalid or expired invitation
                    console.debug('Invitation not found or expired');
                    vm.error = 'This invitation is invalid or has expired.';
                    showToaster('error', 'Invalid Invitation', vm.error);
                    
                    // Redirect to home after a delay
                    $timeout(function() {
                        $state.go('home');
                    }, 3000);
                    break;
                    
                default:
                    // Other error
                    vm.error = response.data.error || 'An error occurred while fetching the invitation details.';
                    showToaster('error', 'Error', vm.error);
            }
        }
        
        /**
         * Accept the team invitation
         */
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
        
        /**
         * Handle successful invitation acceptance
         */
        function handleAcceptSuccess(response) {
            vm.isAccepting = false;
            loaderService.stopLoader();
            
            showToaster('success', 'Success', response.data.message || 'You have successfully joined the team!');
            
            // Clear any stored invitation key
            $window.sessionStorage.removeItem('pendingInvitationKey');
            
            // Redirect to teams page
            $state.go('web.challenge-host-teams');
        }
        
        /**
         * Handle errors when accepting invitation
         */
        function handleAcceptError(response) {
            vm.isAccepting = false;
            loaderService.stopLoader();
            
            vm.error = response.data.error || 'An error occurred while accepting the invitation.';
            showToaster('error', 'Error', vm.error);
            
            // If unauthorized, redirect to login
            if (response.status === 401) {
                vm.isLoggedIn = false;
                redirectToLogin();
            }
        }
        
        /**
         * Redirect to login page and preserve invitation state
         */
        function redirectToLogin() {
            // Store the invitation key in sessionStorage to retrieve after login
            if (vm.invitationKey) {
                console.debug('Storing invitation key before redirecting to login:', vm.invitationKey);
                $window.sessionStorage.setItem('pendingInvitationKey', vm.invitationKey);
            }
            
            // Set previous state for redirection after login (used by AuthCtrl)
            $rootScope.previousState = 'web.challenge-host-team-invitation-accept';
            $rootScope.previousStateParams = { invitation_key: vm.invitationKey };
            
            // Redirect to login page
            $state.go('auth.login');
        }
        
        /**
         * Log out current user to allow login with different account
         */
        function logout() {
            // Keep the invitation key stored
            if (vm.invitationKey) {
                console.debug('Storing invitation key before logout:', vm.invitationKey);
                $window.sessionStorage.setItem('pendingInvitationKey', vm.invitationKey);
            }
            
            // Clear the token from storage
            utilities.deleteData('userKey');
            utilities.deleteData('refreshJWT');
            
            // Update logged in status
            vm.isLoggedIn = false;
            
            // Redirect to login
            $state.go('auth.login');
        }
        
        /**
         * Helper function to show toast notifications
         */
        function showToaster(type, title, message, timeout) {
            toaster.pop({
                type: type,
                title: title,
                body: message,
                timeout: timeout || 5000
            });
        }
        
        // Listen for state change success to handle redirects after login
        $rootScope.$on('$stateChangeSuccess', function(event, toState) {
            console.debug('State changed to:', toState.name);
            // If we're on the invitation page and logged in, but not loading details yet
            if (toState.name === 'web.challenge-host-team-invitation-accept' && 
                vm.isLoggedIn && 
                !vm.isLoading && 
                !vm.invitationDetails.id) {
                console.debug('On invitation page after login, fetching details');
                // Small delay to ensure parameters are fully loaded
                $timeout(function() {
                    fetchInvitationDetails();
                }, 100);
            }
        });
    }
})();
