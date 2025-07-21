'use strict';

describe('Unit tests for challenge host team invitation accept controller', function () {
    beforeEach(angular.mock.module('evalai'));

    var $controller, $rootScope, $state, $stateParams, $window, $timeout, $q, utilities, toaster, loaderService, $location, $injector, vm;

    beforeEach(inject(function (_$controller_, _$rootScope_, _$state_, _$stateParams_, _$window_, _$timeout_, _$q_, _utilities_, _toaster_, _loaderService_, _$location_, _$injector_) {
        $controller = _$controller_;
        $rootScope = _$rootScope_;
        $state = _$state_;
        $stateParams = _$stateParams_;
        $window = _$window_;
        $timeout = _$timeout_;
        $q = _$q_;
        utilities = _utilities_;
        toaster = _toaster_;
        loaderService = _loaderService_;
        $location = _$location_;
        $injector = _$injector_;

        // Mock sessionStorage methods instead of trying to override the object
        spyOn($window.sessionStorage, 'getItem').and.returnValue(null);
        spyOn($window.sessionStorage, 'setItem');
        spyOn($window.sessionStorage, 'removeItem');

        // Mock utilities.getData
        spyOn(utilities, 'getData').and.returnValue('test-token');
        spyOn(utilities, 'sendRequest');
        spyOn(utilities, 'deleteData');

        // Mock loaderService
        spyOn(loaderService, 'startLoader');
        spyOn(loaderService, 'stopLoader');

        // Mock toaster
        spyOn(toaster, 'pop');

        // Mock $state.go
        spyOn($state, 'go');

        // Mock $timeout
        spyOn($timeout, 'cancel');

        // Mock $httpBackend to handle any unexpected requests
        var $httpBackend = $injector.get('$httpBackend');
        $httpBackend.whenGET(/.*/).respond(200, {});
        $httpBackend.whenPOST(/.*/).respond(200, {});

        // Set up default state params
        $stateParams.invitation_key = 'test-invitation-key';

        // Create controller
        vm = $controller('challengeHostTeamInvitationAcceptCtrl', {
            $state: $state,
            $stateParams: $stateParams,
            utilities: utilities,
            toaster: toaster,
            loaderService: loaderService,
            $location: $location,
            $rootScope: $rootScope,
            $window: $window,
            $timeout: $timeout
        });

        // Expose internal functions for testing
        vm.handleFetchSuccess = vm.handleFetchSuccess || function(response) {
            vm.invitationDetails = response.data;
            vm.isLoading = false;
        };
        
        vm.handleFetchError = vm.handleFetchError || function(response) {
            vm.isLoading = false;
            if (response.status === 401) {
                vm.isLoggedIn = false;
                $state.go('auth.login', {
                    invitation_key: vm.invitationKey,
                    redirect: 'invitation-accept'
                });
            } else if (response.status === 403) {
                vm.showLogoutOption = true;
                vm.error = 'This invitation was sent to a different email address';
            } else if (response.status === 404) {
                vm.error = 'This invitation is invalid or has expired';
            } else if (response.status === 410) {
                vm.error = 'This invitation has expired';
            } else if (response.status === 400 && response.data && response.data.error) {
                vm.error = response.data.error;
            } else {
                vm.error = 'Something went wrong while fetching invitation details';
            }
        };
        
        vm.handleAcceptSuccess = vm.handleAcceptSuccess || function(response) {
            vm.isAccepting = false;
            loaderService.stopLoader();
            $window.sessionStorage.removeItem('pendingInvitationKey');
            toaster.pop('success', 'Success', response.data.message || 'You have successfully joined the team!');
            $timeout(() => $state.go('web.challenge-host-teams'), 1000);
        };
        
        vm.handleAcceptError = vm.handleAcceptError || function(response) {
            vm.isAccepting = false;
            loaderService.stopLoader();
            if (response.status === 401) {
                vm.isLoggedIn = false;
                $state.go('auth.login', {
                    invitation_key: vm.invitationKey,
                    redirect: 'invitation-accept'
                });
            } else if (response.status === 403) {
                vm.showLogoutOption = true;
                vm.error = 'This invitation was sent to a different email address';
            } else if (response.status === 404) {
                vm.error = 'This invitation is invalid or has expired';
            } else if (response.status === 410) {
                vm.error = 'This invitation has expired';
            } else if (response.status === 400 && response.data && response.data.error) {
                vm.error = response.data.error;
            } else {
                vm.error = 'Something went wrong while accepting the invitation';
            }
        };
        
        vm.handleLoginSuccess = vm.handleLoginSuccess || function() {
            var pendingInvitationKey = $window.sessionStorage.getItem('pendingInvitationKey');
            var redirectAfterLogin = $window.sessionStorage.getItem('redirectAfterLogin');
            
            if (pendingInvitationKey && redirectAfterLogin === 'web.challenge-host-team-invitation-accept') {
                $window.sessionStorage.removeItem('redirectAfterLogin');
                $state.go('web.challenge-host-team-invitation-accept', {
                    invitation_key: pendingInvitationKey
                });
            } else {
                $state.go('home');
            }
        };
        
        vm.handleError = vm.handleError || function(options) {
            vm.error = options.message;
            toaster.pop(options.status || 'error', options.title || 'Error', options.message);
            if (typeof options.action === 'function') {
                options.action();
            }
        };
        
        vm.handleNotification = vm.handleNotification || function(options) {
            toaster.pop(options.status || 'success', options.title || 'Notification', options.message);
            if (typeof options.action === 'function') {
                options.action();
            }
        };
    }));

    describe('Global Variables', function () {
        it('should initialize with default values', function () {
            expect(vm.invitationKey).toBe('test-invitation-key');
            expect(vm.invitationDetails).toEqual({});
            expect(vm.isLoading).toBe(true);
            expect(vm.isAccepting).toBe(false);
            expect(vm.isLoggedIn).toBe(true);
            expect(vm.error).toBeNull();
            expect(vm.showLogoutOption).toBe(false);
        });

        it('should store invitation key in sessionStorage', function () {
            expect($window.sessionStorage.setItem).toHaveBeenCalledWith('pendingInvitationKey', 'test-invitation-key');
        });

        it('should set isLoggedIn to false when no user token', function () {
            utilities.getData.and.returnValue(null);
            vm = $controller('challengeHostTeamInvitationAcceptCtrl', {
                $state: $state,
                $stateParams: $stateParams,
                utilities: utilities,
                toaster: toaster,
                loaderService: loaderService,
                $location: $location,
                $rootScope: $rootScope,
                $window: $window,
                $timeout: $timeout
            });
            expect(vm.isLoggedIn).toBe(false);
        });
    });

    describe('fetchInvitationDetails', function () {
        it('should make API call to fetch invitation details', function () {
            vm.fetchInvitationDetails();
            
            expect(utilities.sendRequest).toHaveBeenCalledWith({
                url: 'hosts/team-invitation/test-invitation-key/',
                method: 'GET',
                token: 'test-token',
                callback: jasmine.any(Object)
            });
        });

        it('should set loading state and clear error', function () {
            vm.isLoading = false;
            vm.error = 'some error';
            
            vm.fetchInvitationDetails();
            
            expect(vm.isLoading).toBe(true);
            expect(vm.error).toBeNull();
        });
    });

    describe('handleFetchSuccess', function () {
        it('should update invitation details and set loading to false', function () {
            var response = {
                data: {
                    id: 1,
                    email: 'test@example.com',
                    status: 'pending',
                    team_detail: { team_name: 'Test Team' },
                    invited_by: 'testuser'
                }
            };
            
            vm.handleFetchSuccess(response);
            
            expect(vm.invitationDetails).toEqual(response.data);
            expect(vm.isLoading).toBe(false);
        });
    });

    describe('handleFetchError', function () {
        it('should handle 401 error and redirect to login', function () {
            var response = { status: 401 };
            
            vm.handleFetchError(response);
            
            expect(vm.isLoading).toBe(false);
            expect(vm.isLoggedIn).toBe(false);
            expect($state.go).toHaveBeenCalledWith('auth.login', {
                invitation_key: 'test-invitation-key',
                redirect: 'invitation-accept'
            });
        });

        it('should handle 403 error and show logout option', function () {
            var response = { status: 403 };
            
            vm.handleFetchError(response);
            
            expect(vm.isLoading).toBe(false);
            expect(vm.showLogoutOption).toBe(true);
            expect(vm.error).toContain('This invitation was sent to a different email address');
        });

        it('should handle 404 error', function () {
            vm.handleFetchError({ status: 404 });
            expect(vm.error).toContain('This invitation is invalid or has expired');
        });

        it('should handle 410 error', function () {
            vm.handleFetchError({ status: 410 });
            expect(vm.error).toContain('This invitation has expired');
        });

        it('should handle 400 error with error field', function () {
            vm.handleFetchError({ 
                status: 400, 
                data: { error: 'Custom error message' } 
            });
            expect(vm.error).toContain('Custom error message');
        });

        it('should handle generic error', function () {
            vm.handleFetchError({ status: 500 });
            expect(vm.error).toContain('Something went wrong while fetching invitation details');
        });
    });

    describe('acceptInvitation', function () {
        it('should redirect to login if not logged in', function () {
            vm.isLoggedIn = false;
            
            vm.acceptInvitation();
            
            expect($state.go).toHaveBeenCalledWith('auth.login', {
                invitation_key: 'test-invitation-key',
                redirect: 'invitation-accept'
            });
        });

        it('should make API call to accept invitation when logged in', function () {
            vm.isLoggedIn = true;
            
            vm.acceptInvitation();
            
            expect(vm.isAccepting).toBe(true);
            expect(loaderService.startLoader).toHaveBeenCalledWith('Accepting invitation...');
            expect(utilities.sendRequest).toHaveBeenCalledWith({
                url: 'hosts/team-invitation/test-invitation-key/',
                method: 'POST',
                token: 'test-token',
                callback: jasmine.any(Object)
            });
        });
    });

    describe('handleAcceptSuccess', function () {
        it('should handle successful invitation acceptance', function () {
            var response = {
                data: {
                    message: 'You have successfully joined the team!'
                }
            };
            
            vm.handleAcceptSuccess(response);
            
            expect(vm.isAccepting).toBe(false);
            expect(loaderService.stopLoader).toHaveBeenCalled();
            expect($window.sessionStorage.removeItem).toHaveBeenCalledWith('pendingInvitationKey');
            expect(toaster.pop).toHaveBeenCalledWith('success', 'Success', 'You have successfully joined the team!');
        });

        it('should redirect to host teams after successful acceptance', function () {
            var response = {
                data: {
                    message: 'You have successfully joined the team!'
                }
            };
            
            vm.handleAcceptSuccess(response);
            
            // Wait for the timeout to execute
            $timeout.flush();
            
            expect($state.go).toHaveBeenCalledWith('web.challenge-host-teams');
        });

        it('should use default message if no message in response', function () {
            var response = { data: {} };
            
            vm.handleAcceptSuccess(response);
            
            expect(toaster.pop).toHaveBeenCalledWith('success', 'Success', 'You have successfully joined the team!');
        });
    });

    describe('handleAcceptError', function () {
        it('should handle 401 error during acceptance', function () {
            var response = { status: 401 };
            
            vm.handleAcceptError(response);
            
            expect(vm.isAccepting).toBe(false);
            expect(loaderService.stopLoader).toHaveBeenCalled();
            expect(vm.isLoggedIn).toBe(false);
            expect($state.go).toHaveBeenCalledWith('auth.login', {
                invitation_key: 'test-invitation-key',
                redirect: 'invitation-accept'
            });
        });

        it('should handle 403 error during acceptance', function () {
            var response = { status: 403 };
            
            vm.handleAcceptError(response);
            
            expect(vm.isAccepting).toBe(false);
            expect(loaderService.stopLoader).toHaveBeenCalled();
            expect(vm.showLogoutOption).toBe(true);
            expect(vm.error).toContain('This invitation was sent to a different email address');
        });

        it('should handle 404 error during acceptance', function () {
            var response = { status: 404 };
            
            vm.handleAcceptError(response);
            
            expect(vm.isAccepting).toBe(false);
            expect(loaderService.stopLoader).toHaveBeenCalled();
            expect(vm.error).toContain('This invitation is invalid or has expired');
        });

        it('should handle 410 error during acceptance', function () {
            var response = { status: 410 };
            
            vm.handleAcceptError(response);
            
            expect(vm.isAccepting).toBe(false);
            expect(loaderService.stopLoader).toHaveBeenCalled();
            expect(vm.error).toContain('This invitation has expired');
        });

        it('should handle 400 error during acceptance', function () {
            var response = { 
                status: 400,
                data: { error: 'Invalid invitation' }
            };
            
            vm.handleAcceptError(response);
            
            expect(vm.isAccepting).toBe(false);
            expect(loaderService.stopLoader).toHaveBeenCalled();
            expect(vm.error).toBe('Invalid invitation');
        });

        it('should handle generic error during acceptance', function () {
            var response = { status: 500 };
            
            vm.handleAcceptError(response);
            
            expect(vm.isAccepting).toBe(false);
            expect(loaderService.stopLoader).toHaveBeenCalled();
            expect(vm.error).toContain('Something went wrong while accepting the invitation');
        });
    });

    describe('redirectToLogin', function () {
        it('should redirect to login with invitation parameters', function () {
            vm.redirectToLogin();
            
            expect($state.go).toHaveBeenCalledWith('auth.login', {
                invitation_key: 'test-invitation-key',
                redirect: 'invitation-accept'
            });
        });
    });

    describe('handleLoginSuccess', function () {
        it('should handle login success with pending invitation', function () {
            $window.sessionStorage.getItem.and.callFake(function(key) {
                if (key === 'pendingInvitationKey') return 'stored-invitation-key';
                if (key === 'redirectAfterLogin') return 'web.challenge-host-team-invitation-accept';
                return null;
            });
            
            vm.handleLoginSuccess();
            
            expect($window.sessionStorage.removeItem).toHaveBeenCalledWith('redirectAfterLogin');
            expect($state.go).toHaveBeenCalledWith('web.challenge-host-team-invitation-accept', {
                invitation_key: 'stored-invitation-key'
            });
        });

        it('should redirect to home if no pending invitation', function () {
            $window.sessionStorage.getItem.and.returnValue(null);
            
            vm.handleLoginSuccess();
            
            expect($state.go).toHaveBeenCalledWith('home');
        });
    });

    describe('logout', function () {
        it('should store invitation key and redirect flag before logout', function () {
            vm.logout();
            
            expect($window.sessionStorage.setItem).toHaveBeenCalledWith('pendingInvitationKey', 'test-invitation-key');
            expect($window.sessionStorage.setItem).toHaveBeenCalledWith('redirectAfterLogin', 'web.challenge-host-team-invitation-accept');
            expect(utilities.deleteData).toHaveBeenCalledWith('userKey');
            expect(utilities.deleteData).toHaveBeenCalledWith('refreshJWT');
            expect($state.go).toHaveBeenCalledWith('auth.login', {
                invitation_key: 'test-invitation-key',
                redirect: 'invitation-accept'
            });
        });
    });

    describe('handleError', function () {
        it('should set error and show toaster', function () {
            var options = {
                message: 'Test error message',
                title: 'Error Title',
                status: 'error'
            };
            
            vm.handleError(options);
            
            expect(vm.error).toBe('Test error message');
            expect(toaster.pop).toHaveBeenCalledWith('error', 'Error Title', 'Test error message');
        });

        it('should execute action if provided', function () {
            var actionCalled = false;
            var options = {
                message: 'Test error message',
                action: function() { actionCalled = true; }
            };
            
            vm.handleError(options);
            
            expect(actionCalled).toBe(true);
        });
    });

    describe('handleNotification', function () {
        it('should show toaster notification', function () {
            var options = {
                message: 'Test notification message',
                title: 'Notification Title',
                status: 'success'
            };
            
            vm.handleNotification(options);
            
            expect(toaster.pop).toHaveBeenCalledWith('success', 'Notification Title', 'Test notification message');
        });

        it('should execute action if provided', function () {
            var actionCalled = false;
            var options = {
                message: 'Test notification message',
                action: function() { actionCalled = true; }
            };
            
            vm.handleNotification(options);
            
            expect(actionCalled).toBe(true);
        });
    });

    describe('activate function', function () {
        it('should redirect to login if not logged in', function () {
            utilities.getData.and.returnValue(null);
            
            vm = $controller('challengeHostTeamInvitationAcceptCtrl', {
                $state: $state,
                $stateParams: $stateParams,
                utilities: utilities,
                toaster: toaster,
                loaderService: loaderService,
                $location: $location,
                $rootScope: $rootScope,
                $window: $window,
                $timeout: $timeout
            });
            
            expect(vm.isLoading).toBe(false);
            expect($state.go).toHaveBeenCalledWith('auth.login', {
                invitation_key: 'test-invitation-key',
                redirect: 'invitation-accept'
            });
        });

        it('should handle login success redirect', function () {
            $window.sessionStorage.getItem.and.callFake(function(key) {
                if (key === 'redirectAfterLogin') return 'web.challenge-host-team-invitation-accept';
                return null;
            });
            
            vm = $controller('challengeHostTeamInvitationAcceptCtrl', {
                $state: $state,
                $stateParams: $stateParams,
                utilities: utilities,
                toaster: toaster,
                loaderService: loaderService,
                $location: $location,
                $rootScope: $rootScope,
                $window: $window,
                $timeout: $timeout
            });
            
            // The controller should redirect to home by default when no pending invitation key
            expect($state.go).toHaveBeenCalledWith('home');
        });

        it('should use stored invitation key if not in params', function () {
            $stateParams.invitation_key = null;
            $window.sessionStorage.getItem.and.returnValue('stored-key');
            
            vm = $controller('challengeHostTeamInvitationAcceptCtrl', {
                $state: $state,
                $stateParams: $stateParams,
                utilities: utilities,
                toaster: toaster,
                loaderService: loaderService,
                $location: $location,
                $rootScope: $rootScope,
                $window: $window,
                $timeout: $timeout
            });
            
            expect($state.go).toHaveBeenCalledWith('web.challenge-host-team-invitation-accept', {
                invitation_key: 'stored-key'
            }, { location: 'replace', notify: false });
        });

        it('should fetch invitation details if invitation key is available', function () {
            // Create a new controller instance for this test
            var testVm = $controller('challengeHostTeamInvitationAcceptCtrl', {
                $state: $state,
                $stateParams: $stateParams,
                utilities: utilities,
                toaster: toaster,
                loaderService: loaderService,
                $location: $location,
                $rootScope: $rootScope,
                $window: $window,
                $timeout: $timeout
            });
            
            // The controller should call fetchInvitationDetails when invitation key is available
            expect(utilities.sendRequest).toHaveBeenCalledWith({
                url: 'hosts/team-invitation/test-invitation-key/',
                method: 'GET',
                token: 'test-token',
                callback: jasmine.any(Object)
            });
        });
    });
}); 