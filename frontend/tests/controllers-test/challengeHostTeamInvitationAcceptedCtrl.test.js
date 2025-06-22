describe('challengeHostTeamInvitationAcceptCtrl', function() {
    var $controller, $scope, $rootScope, $state, $stateParams, $window, $timeout;
    var utilities, toaster, loaderService, vm;
    var mockUserKey, mockInvitationKey;

    beforeEach(function() {
        module('evalai');
        
        inject(function(_$controller_, _$rootScope_, _$state_, _$timeout_, _$window_) {
            $controller = _$controller_;
            $rootScope = _$rootScope_;
            $scope = $rootScope.$new();
            $state = _$state_;
            $timeout = _$timeout_;
            $window = _$window_;
        });

        // Mock dependencies
        $stateParams = { invitation_key: 'test-invitation-key' };
        mockUserKey = 'mock-user-key';
        mockInvitationKey = 'test-invitation-key';

        utilities = {
            getData: jasmine.createSpy('getData').and.returnValue(mockUserKey),
            sendRequest: jasmine.createSpy('sendRequest'),
            deleteData: jasmine.createSpy('deleteData')
        };

        toaster = {
            pop: jasmine.createSpy('pop')
        };

        loaderService = {
            startLoader: jasmine.createSpy('startLoader'),
            stopLoader: jasmine.createSpy('stopLoader')
        };

        // Mock sessionStorage
        $window.sessionStorage = {
            getItem: jasmine.createSpy('getItem').and.returnValue(null),
            setItem: jasmine.createSpy('setItem'),
            removeItem: jasmine.createSpy('removeItem')
        };

        spyOn($state, 'go');
    });

    function createController() {
        vm = $controller('challengeHostTeamInvitationAcceptCtrl', {
            $state: $state,
            $stateParams: $stateParams,
            utilities: utilities,
            toaster: toaster,
            loaderService: loaderService,
            $location: {},
            $rootScope: $rootScope,
            $window: $window,
            $timeout: $timeout
        });
        return vm;
    }

    // Test 1: Controller Initialization - Logged In User
    describe('Controller Initialization - Logged In User', function() {
        beforeEach(function() {
            utilities.getData.and.returnValue(mockUserKey);
            utilities.sendRequest.and.callFake(function(params) {
                params.callback.onSuccess({
                    data: { team_name: 'Test Team', inviter_email: 'test@example.com' }
                });
            });
        });

        it('should initialize with correct default values', function() {
            vm = createController();

            expect(vm.invitationKey).toBe('test-invitation-key');
            expect(vm.isLoggedIn).toBe(true);
            expect(vm.isLoading).toBe(true);
            expect(vm.isAccepting).toBe(false);
            expect(vm.error).toBe(null);
            expect(vm.showLogoutOption).toBe(false);
            expect(vm.invitationDetails).toEqual({});
        });

        it('should store invitation key in sessionStorage', function() {
            vm = createController();

            expect($window.sessionStorage.setItem).toHaveBeenCalledWith(
                'pendingInvitationKey', 
                'test-invitation-key'
            );
        });

        it('should fetch invitation details on initialization', function() {
            vm = createController();

            expect(utilities.sendRequest).toHaveBeenCalledWith(jasmine.objectContaining({
                url: 'hosts/team-invitation/test-invitation-key/',
                method: 'GET',
                token: mockUserKey
            }));
        });
    });

    // Test 2: Controller Initialization - Not Logged In
    describe('Controller Initialization - Not Logged In', function() {
        beforeEach(function() {
            utilities.getData.and.returnValue(null);
        });

        it('should redirect to login when user not logged in', function() {
            vm = createController();

            expect(vm.isLoggedIn).toBe(false);
            expect(vm.isLoading).toBe(false);
            expect($state.go).toHaveBeenCalledWith('auth.login', {
                invitation_key: 'test-invitation-key',
                redirect: 'invitation-accept'
            });
        });

        it('should store invitation key and redirect state in sessionStorage', function() {
            vm = createController();

            expect($window.sessionStorage.setItem).toHaveBeenCalledWith(
                'pendingInvitationKey', 
                'test-invitation-key'
            );
            expect($window.sessionStorage.setItem).toHaveBeenCalledWith(
                'redirectAfterLogin', 
                'web.challenge-host-team-invitation-accept'
            );
        });
    });

    // Test 3: Post-Login Redirect Handling
    describe('Post-Login Redirect Handling', function() {
        beforeEach(function() {
            utilities.getData.and.returnValue(mockUserKey);
            $window.sessionStorage.getItem.and.callFake(function(key) {
                if (key === 'redirectAfterLogin') return 'web.challenge-host-team-invitation-accept';
                if (key === 'pendingInvitationKey') return 'stored-invitation-key';
                return null;
            });
        });

        it('should handle login success redirect correctly', function() {
            vm = createController();

            expect($window.sessionStorage.removeItem).toHaveBeenCalledWith('redirectAfterLogin');
            expect($state.go).toHaveBeenCalledWith('web.challenge-host-team-invitation-accept', {
                invitation_key: 'stored-invitation-key'
            });
        });
    });

    // Test 4: Missing Invitation Key Handling
    describe('Missing Invitation Key Handling', function() {
        beforeEach(function() {
            utilities.getData.and.returnValue(mockUserKey);
            $stateParams.invitation_key = null;
            $window.sessionStorage.getItem.and.callFake(function(key) {
                if (key === 'pendingInvitationKey') return 'stored-invitation-key';
                return null;
            });
        });

        it('should restore invitation key from sessionStorage and redirect', function() {
            vm = createController();

            expect(vm.invitationKey).toBe('stored-invitation-key');
            expect($state.go).toHaveBeenCalledWith(
                'web.challenge-host-team-invitation-accept',
                { invitation_key: 'stored-invitation-key' },
                { location: 'replace', notify: false }
            );
        });
    });

    // Test 5: Fetch Invitation Details Success
    describe('Fetch Invitation Details', function() {
        beforeEach(function() {
            utilities.getData.and.returnValue(mockUserKey);
        });

        it('should handle successful invitation fetch', function() {
            var mockResponse = {
                data: {
                    team_name: 'Test Team',
                    inviter_email: 'inviter@example.com',
                    created: '2025-01-01'
                }
            };

            utilities.sendRequest.and.callFake(function(params) {
                params.callback.onSuccess(mockResponse);
            });

            vm = createController();

            expect(vm.invitationDetails).toEqual(mockResponse.data);
            expect(vm.isLoading).toBe(false);
        });

        it('should start with loading state during fetch', function() {
            utilities.sendRequest.and.callFake(function(params) {
                expect(vm.isLoading).toBe(true);
                expect(vm.error).toBe(null);
            });

            vm = createController();
        });
    });

    // Test 6: Fetch Invitation Details Error Handling
    describe('Fetch Invitation Details Error Handling', function() {
        beforeEach(function() {
            utilities.getData.and.returnValue(mockUserKey);
        });

        it('should handle 401 authentication error', function() {
            utilities.sendRequest.and.callFake(function(params) {
                params.callback.onError({ status: 401 });
            });

            vm = createController();

            expect(vm.isLoading).toBe(false);
            expect(vm.error).toBe('You need to log in to view this invitation.');
            expect(toaster.pop).toHaveBeenCalledWith(jasmine.objectContaining({
                type: 'warning'
            }));
            expect(vm.isLoggedIn).toBe(false);
        });

        it('should handle 403 wrong account error', function() {
            utilities.sendRequest.and.callFake(function(params) {
                params.callback.onError({ status: 403 });
            });

            vm = createController();

            expect(vm.error).toBe('This invitation was sent to a different email address. Please log in with the correct account.');
            expect(vm.showLogoutOption).toBe(true);
            expect(toaster.pop).toHaveBeenCalledWith(jasmine.objectContaining({
                type: 'error'
            }));
        });

        it('should handle 404 invalid invitation error', function() {
            utilities.sendRequest.and.callFake(function(params) {
                params.callback.onError({ status: 404 });
            });

            vm = createController();
            $timeout.flush();

            expect(vm.error).toBe('This invitation is invalid or has expired.');
            expect($state.go).toHaveBeenCalledWith('home');
        });

        it('should handle generic error', function() {
            var mockError = {
                status: 500,
                data: { error: 'Server error occurred' }
            };

            utilities.sendRequest.and.callFake(function(params) {
                params.callback.onError(mockError);
            });

            vm = createController();

            expect(vm.error).toBe('Server error occurred');
            expect(toaster.pop).toHaveBeenCalledWith(jasmine.objectContaining({
                type: 'error'
            }));
        });
    });

    // Test 7: Accept Invitation Success
    describe('Accept Invitation', function() {
        beforeEach(function() {
            utilities.getData.and.returnValue(mockUserKey);
            // Mock initial fetch success
            utilities.sendRequest.and.callFake(function(params) {
                if (params.method === 'GET') {
                    params.callback.onSuccess({ data: { team_name: 'Test Team' } });
                }
            });
            vm = createController();
        });

        it('should handle successful invitation acceptance', function() {
            var mockAcceptResponse = {
                data: { message: 'Successfully joined the team!' }
            };

            utilities.sendRequest.and.callFake(function(params) {
                if (params.method === 'POST') {
                    params.callback.onSuccess(mockAcceptResponse);
                }
            });

            vm.acceptInvitation();

            expect(vm.isAccepting).toBe(false);
            expect(loaderService.startLoader).toHaveBeenCalledWith('Accepting invitation...');
            expect(loaderService.stopLoader).toHaveBeenCalled();
            expect($window.sessionStorage.removeItem).toHaveBeenCalledWith('pendingInvitationKey');
            expect($state.go).toHaveBeenCalledWith('web.challenge-host-teams');
        });

        it('should redirect to login if not logged in during acceptance', function() {
            vm.isLoggedIn = false;
            vm.acceptInvitation();

            expect($state.go).toHaveBeenCalledWith('auth.login', jasmine.any(Object));
        });

        it('should set accepting state during API call', function() {
            utilities.sendRequest.and.callFake(function(params) {
                expect(vm.isAccepting).toBe(true);
                expect(loaderService.startLoader).toHaveBeenCalledWith('Accepting invitation...');
            });

            vm.acceptInvitation();
        });
    });

    // Test 8: Accept Invitation Error Handling
    describe('Accept Invitation Error Handling', function() {
        beforeEach(function() {
            utilities.getData.and.returnValue(mockUserKey);
            utilities.sendRequest.and.callFake(function(params) {
                if (params.method === 'GET') {
                    params.callback.onSuccess({ data: { team_name: 'Test Team' } });
                }
            });
            vm = createController();
        });

        it('should handle 401 session expired error during acceptance', function() {
            utilities.sendRequest.and.callFake(function(params) {
                if (params.method === 'POST') {
                    params.callback.onError({ status: 401 });
                }
            });

            vm.acceptInvitation();

            expect(vm.isAccepting).toBe(false);
            expect(loaderService.stopLoader).toHaveBeenCalled();
            expect(vm.isLoggedIn).toBe(false);
            expect($state.go).toHaveBeenCalledWith('auth.login', jasmine.any(Object));
        });

        it('should handle generic acceptance error', function() {
            var mockError = {
                status: 500,
                data: { error: 'Team is full' }
            };

            utilities.sendRequest.and.callFake(function(params) {
                if (params.method === 'POST') {
                    params.callback.onError(mockError);
                }
            });

            vm.acceptInvitation();

            expect(vm.isAccepting).toBe(false);
            expect(loaderService.stopLoader).toHaveBeenCalled();
            expect(toaster.pop).toHaveBeenCalledWith(jasmine.objectContaining({
                type: 'error'
            }));
        });
    });

    // Test 9: Logout Functionality
    describe('Logout Functionality', function() {
        beforeEach(function() {
            utilities.getData.and.returnValue(mockUserKey);
            utilities.sendRequest.and.callFake(function(params) {
                params.callback.onSuccess({ data: { team_name: 'Test Team' } });
            });
            vm = createController();
        });

        it('should preserve invitation context during logout', function() {
            vm.logout();

            expect($window.sessionStorage.setItem).toHaveBeenCalledWith(
                'pendingInvitationKey', 
                vm.invitationKey
            );
            expect($window.sessionStorage.setItem).toHaveBeenCalledWith(
                'redirectAfterLogin', 
                'web.challenge-host-team-invitation-accept'
            );
        });

        it('should clear user authentication data', function() {
            vm.logout();

            expect(utilities.deleteData).toHaveBeenCalledWith('userKey');
            expect(utilities.deleteData).toHaveBeenCalledWith('refreshJWT');
        });

        it('should redirect to login with invitation context', function() {
            vm.logout();

            expect($state.go).toHaveBeenCalledWith('auth.login', {
                invitation_key: vm.invitationKey,
                redirect: 'invitation-accept'
            });
        });
    });

    // Test 10: Toaster Notification System
    describe('Toaster Notification System', function() {
        beforeEach(function() {
            utilities.getData.and.returnValue(mockUserKey);
            utilities.sendRequest.and.callFake(function(params) {
                params.callback.onSuccess({ data: { team_name: 'Test Team' } });
            });
            vm = createController();
        });

        it('should display styled error notifications', function() {
            var config = {
                title: 'Test Error',
                message: 'Test error message',
                status: 'error',
                timeout: 5000,
                dismissButton: true
            };

            vm.displayErrorNotification(config);

            expect(toaster.pop).toHaveBeenCalledWith(jasmine.objectContaining({
                type: 'error',
                bodyOutputType: 'trustedHtml',
                timeout: 5000,
                dismissButton: true,
                positionClass: 'toast-top-right'
            }));
        });

        it('should display success notifications', function() {
            vm.showToaster('success', 'Success Title', 'Success message', 3000);

            expect(toaster.pop).toHaveBeenCalledWith(jasmine.objectContaining({
                type: 'success',
                timeout: 3000,
                dismissButton: true
            }));
        });
    });

    // Test 11: Edge Cases and Error Recovery
    describe('Edge Cases and Error Recovery', function() {
        it('should handle missing invitation key gracefully', function() {
            $stateParams.invitation_key = null;
            utilities.getData.and.returnValue(mockUserKey);
            $window.sessionStorage.getItem.and.returnValue(null);

            vm = createController();

            expect(utilities.sendRequest).not.toHaveBeenCalled();
        });

        it('should handle malformed error responses', function() {
            utilities.getData.and.returnValue(mockUserKey);
            utilities.sendRequest.and.callFake(function(params) {
                params.callback.onError({ status: 500, data: null });
            });

            vm = createController();

            expect(vm.error).toBe('An error occurred while fetching the invitation details.');
        });

        it('should handle network failures during acceptance', function() {
            utilities.getData.and.returnValue(mockUserKey);
            utilities.sendRequest.and.callFake(function(params) {
                if (params.method === 'GET') {
                    params.callback.onSuccess({ data: { team_name: 'Test Team' } });
                } else if (params.method === 'POST') {
                    params.callback.onError({ status: 0, data: {} });
                }
            });

            vm = createController();
            vm.acceptInvitation();

            expect(vm.isAccepting).toBe(false);
            expect(toaster.pop).toHaveBeenCalled();
        });
    });

    // Test 12: Complete User Workflows
    describe('Complete User Workflows', function() {
        it('should complete full logged-in acceptance workflow', function() {
            // Setup: User is logged in, invitation exists
            utilities.getData.and.returnValue(mockUserKey);
            utilities.sendRequest.and.callFake(function(params) {
                if (params.method === 'GET') {
                    params.callback.onSuccess({ 
                        data: { team_name: 'Test Team', inviter_email: 'test@example.com' } 
                    });
                } else if (params.method === 'POST') {
                    params.callback.onSuccess({ 
                        data: { message: 'Welcome to the team!' } 
                    });
                }
            });

            // Step 1: Initialize controller
            vm = createController();
            expect(vm.isLoading).toBe(false);
            expect(vm.invitationDetails.team_name).toBe('Test Team');

            // Step 2: Accept invitation
            vm.acceptInvitation();
            expect($window.sessionStorage.removeItem).toHaveBeenCalledWith('pendingInvitationKey');
            expect($state.go).toHaveBeenCalledWith('web.challenge-host-teams');
        });

        it('should complete full login-required workflow', function() {
            // Setup: User not logged in initially
            utilities.getData.and.returnValue(null);

            // Step 1: Initialize controller (should redirect to login)
            vm = createController();
            expect($state.go).toHaveBeenCalledWith('auth.login', jasmine.any(Object));

            // Step 2: Simulate post-login return
            utilities.getData.and.returnValue('new-user-key');
            $window.sessionStorage.getItem.and.callFake(function(key) {
                if (key === 'redirectAfterLogin') return 'web.challenge-host-team-invitation-accept';
                if (key === 'pendingInvitationKey') return 'test-invitation-key';
                return null;
            });

            vm = createController();
            expect($state.go).toHaveBeenCalledWith('web.challenge-host-team-invitation-accept', {
                invitation_key: 'test-invitation-key'
            });
        });
    });
});
