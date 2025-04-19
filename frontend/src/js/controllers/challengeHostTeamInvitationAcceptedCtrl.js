(function () {
    'use strict';

    angular
        .module('evalai')
        .controller('challengeHostTeamInvitationAcceptCtrl', challengeHostTeamInvitationAcceptCtrl);

    challengeHostTeamInvitationAcceptCtrl.$inject = ['$state', '$stateParams', 'utilities', 'toaster', 'loaderService', '$location', '$rootScope'];

    function challengeHostTeamInvitationAcceptCtrl($state, $stateParams, utilities, toaster, loaderService, $location, $rootScope) {
        var vm = this;
        var userKey = utilities.getData('userKey'); // Get token from utilities instead of AuthService
        
        // Variables
        vm.invitationKey = $stateParams.invitation_key;
        vm.invitationDetails = {};
        vm.isLoading = true;
        vm.isAccepting = false;
        vm.isLoggedIn = !!userKey; // Check if user is logged in based on token existence
        vm.error = null;
        
        // Functions
        vm.fetchInvitationDetails = fetchInvitationDetails;
        vm.acceptInvitation = acceptInvitation;
        vm.redirectToLogin = redirectToLogin;
        vm.logout = logout;
        
        // Initialize
        activate();
        
        function activate() {
            // Check if we just logged in and have a pending invitation
            var storedInvitationKey = localStorage.getItem('pendingInvitationKey');
            
            // If we have a stored key and no key in the URL, redirect to the proper URL
            if (storedInvitationKey && !vm.invitationKey) {
                localStorage.removeItem('pendingInvitationKey');
                $state.go('web.challenge-host-team-invitation-accept', {invitation_key: storedInvitationKey});
                return;
            }
            
            if (vm.isLoggedIn) {
                fetchInvitationDetails();
            } else {
                vm.isLoading = false;
                // If not logged in, store the current invitation key and redirect to login
                redirectToLogin();
            }
        }
        
        function fetchInvitationDetails() {
            vm.isLoading = true;
            vm.error = null;
            
            var parameters = {
                url: 'team-invitation/' + vm.invitationKey,
                method: 'GET',
                token: userKey,
                callback: {
                    onSuccess: function(response) {
                        vm.invitationDetails = response.data;
                        vm.isLoading = false;
                        
                        // Clear the stored invitation key if it exists
                        if (localStorage.getItem('pendingInvitationKey') === vm.invitationKey) {
                            localStorage.removeItem('pendingInvitationKey');
                        }
                    },
                    onError: function(response) {
                        vm.isLoading = false;
                        
                        if (response.status === 401) {
                            // User needs to log in
                            vm.isLoggedIn = false;
                            redirectToLogin();
                        } else if (response.status === 403) {
                            // Wrong user logged in
                            vm.error = 'This invitation was sent to a different email address. Please log in with the correct account.';
                            toaster.pop({
                                type: 'error',
                                title: 'Wrong Account',
                                body: vm.error,
                                timeout: 5000
                            });
                            
                            // Option to logout and try with another account
                            vm.showLogoutOption = true;
                        } else if (response.status === 404) {
                            // Invalid or expired invitation
                            vm.error = 'This invitation is invalid or has expired.';
                            toaster.pop({
                                type: 'error',
                                title: 'Invalid Invitation',
                                body: vm.error,
                                timeout: 5000
                            });
                            
                            // Redirect to home after a delay
                            setTimeout(function() {
                                $state.go('home');
                            }, 3000);
                        } else {
                            // Other error
                            vm.error = response.data.error || 'An error occurred while fetching the invitation details.';
                            toaster.pop({
                                type: 'error',
                                title: 'Error',
                                body: vm.error,
                                timeout: 5000
                            });
                        }
                    }
                }
            };
            
            utilities.sendRequest(parameters);
        }
        
        function acceptInvitation() {
            if (!vm.isLoggedIn) {
                redirectToLogin();
                return;
            }
            
            vm.isAccepting = true;
            loaderService.startLoader('Accepting invitation...');
            
            var parameters = {
                url: 'team-invitation/' + vm.invitationKey,
                method: 'POST',
                token: userKey,
                callback: {
                    onSuccess: function(response) {
                        vm.isAccepting = false;
                        loaderService.stopLoader();
                        
                        toaster.pop({
                            type: 'success',
                            title: 'Success',
                            body: response.data.message || 'You have successfully joined the team!',
                            timeout: 5000
                        });
                        
                        // Clear any stored invitation key
                        localStorage.removeItem('pendingInvitationKey');
                        
                        // Redirect to teams page or dashboard
                        $state.go('web.challenge-host-teams');
                    },
                    onError: function(response) {
                        vm.isAccepting = false;
                        loaderService.stopLoader();
                        
                        vm.error = response.data.error || 'An error occurred while accepting the invitation.';
                        toaster.pop({
                            type: 'error',
                            title: 'Error',
                            body: vm.error,
                            timeout: 5000
                        });
                        
                        // If unauthorized, redirect to login
                        if (response.status === 401) {
                            vm.isLoggedIn = false;
                            redirectToLogin();
                        }
                    }
                }
            };
            
            utilities.sendRequest(parameters);
        }
        
        function redirectToLogin() {
            // Store the invitation key in localStorage to retrieve after login
            localStorage.setItem('pendingInvitationKey', vm.invitationKey);
            
            // Store the current URL to redirect back after login
            localStorage.setItem('redirectAfterLogin', $location.absUrl());
            
            // Set previous state for redirection after login (used by AuthCtrl)
            $rootScope.previousState = 'web.challenge-host-team-invitation-accept';
            $rootScope.previousStateParams = { invitation_key: vm.invitationKey };
            
            // Redirect to login page
            $state.go('auth.login');
        }
        
        function logout() {
            // Keep the invitation key stored
            localStorage.setItem('pendingInvitationKey', vm.invitationKey);
            
            // Clear the token from storage
            utilities.deleteData('userKey');
            utilities.deleteData('refreshJWT');
            
            // Update logged in status
            vm.isLoggedIn = false;
            
            // Redirect to login
            $state.go('auth.login');
        }
    }
})();
