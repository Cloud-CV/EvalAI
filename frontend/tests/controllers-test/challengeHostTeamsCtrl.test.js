'use strict';

describe('Unit tests for challenge host team controller', function () {
    beforeEach(angular.mock.module('evalai'));

    var $controller, createController, $injector, $mdDialog, $rootScope, $state, $scope, loaderService, utilities, $http, $compile, vm, $timeout;

    beforeEach(inject(function (_$controller_, _$injector_, _$mdDialog_, _$rootScope_, _$state_, _utilities_, _loaderService_, _$http_, _$compile_, _$timeout_) {
        $controller = _$controller_;
        $injector = _$injector_;
        $rootScope = _$rootScope_;
        $state = _$state_;
        utilities = _utilities_;
        loaderService = _loaderService_;
        $http = _$http_;
        $mdDialog = _$mdDialog_;
        $compile = _$compile_;
        $timeout = _$timeout_;

        $scope = $rootScope.$new();
        createController = function () {
            return $controller('ChallengeHostTeamsCtrl', { $scope: $scope });
        };
        vm = $controller('ChallengeHostTeamsCtrl', { $scope: $scope });
    }));

    describe('Global variables', function () {
        it('has default values', function () {
            spyOn(utilities, 'getData');
            spyOn(utilities, 'showLoader');
            utilities.storeData('userKey', 'encrypted key');
            vm = createController();

            expect(utilities.getData).toHaveBeenCalledWith('userKey');
            expect(utilities.showLoader).toHaveBeenCalled();
            expect(vm.teamId).toBeNull();
            expect(vm.existTeam).toEqual({});
            expect(vm.currentPage).toEqual('');
            expect(vm.isNext).toEqual('');
            expect(vm.isPrev).toEqual('');
            expect(vm.team.error).toBeFalsy();
            expect(vm.showPagination).toBeFalsy();
            expect(vm.hostTeamId).toBeNull(null);
            expect(vm.challengeHostTeamId).toBeNull(null);
            expect(vm.isExistLoader).toBeFalsy();
            expect(vm.loaderTitle).toEqual('');
        });
    });

    describe('Validate helper functions', function () {
        it('startLoader', function () {
            var message = 'Start Loader';
            vm = createController();
            vm.startLoader(message);
            expect(vm.isExistLoader).toEqual(true);
            expect(vm.loaderTitle).toEqual(message);
        });

        it('stopLoader', function () {
            var message = '';
            vm = createController();
            vm.stopLoader();
            expect(vm.isExistLoader).toEqual(false);
            expect(vm.loaderTitle).toEqual(message);
        });

        it('activateCollapsible should initialize collapsible elements', function () {
            vm = createController();
            var mockElement = {
                collapsible: jasmine.createSpy('collapsible')
            };
            spyOn(angular, 'element').and.returnValue(mockElement);
            
            vm.activateCollapsible();
            
            expect(angular.element).toHaveBeenCalledWith('.collapsible');
            expect(mockElement.collapsible).toHaveBeenCalled();
        });
    });

    describe('Unit tests for global backend calls', function () {
        var success, successResponse, errorResponse;
        var hostTeamList = [
            {
                next: null,
                previous: null,
            },
            {
                next: null,
                previous: null,
            },
            {
                next: 'page=5',
                previous: null,
            },
            {
                next: null,
                previous: 'page=3',
            },
            {
                next: 'page=4',
                previous: 'page=2',
            }
        ];

        beforeEach(function () {
            spyOn(utilities, 'deleteData');
            spyOn(utilities, 'storeData');
            spyOn(utilities, 'hideLoader');

            utilities.sendRequest = function (parameters) {
                if (success) {
                    parameters.callback.onSuccess({
                        data: successResponse,
                        status: 200
                    });
                } else {
                    parameters.callback.onError({
                        data: errorResponse
                    });
                }
            };
        });

        hostTeamList.forEach(response => {
            it('when pagination next is ' + response.next + 'and previous is ' + response.previous + '\
            `hosts/challenge_host_team/`', function () {
                ;
                success = true;
                successResponse = response;
                vm = createController();
                expect(vm.existTeam).toEqual(successResponse);
                expect(vm.showPagination).toBeTruthy();
                expect(vm.paginationMsg).toEqual('');
                expect(utilities.deleteData).toHaveBeenCalledWith('emailError');

                if (vm.existTeam.next == null) {
                    expect(vm.isNext).toEqual('disabled');
                    expect(vm.currentPage).toEqual(1);
                } else {
                    expect(vm.isNext).toEqual('');
                    expect(vm.currentPage).toEqual(vm.existTeam.next.split('page=')[1] - 1);
                }

                if (vm.existTeam.previous == null) {
                    expect(vm.isPrev).toEqual('disabled');
                } else {
                    expect(vm.isPrev).toEqual('');
                }

                if (vm.existTeam.next !== null) {
                    expect(vm.currentPage).toEqual(vm.existTeam.next.split('page=')[1] - 1);
                } else {
                    expect(vm.currentPage).toEqual(1);
                }
            });
        });

        it('when initial load returns zero teams', function () {
            success = true;
            successResponse = {
                count: 0,
                next: null,
                previous: null,
                results: []
            };
            vm = createController();
            expect(vm.existTeam).toEqual(successResponse);
            expect(vm.showPagination).toBeFalsy();
            expect(vm.paginationMsg).toEqual("No team exists for now. Start by creating a new team!");
        });

        it('backend error of listing challenge host team `hosts/challenge_host_team/`', function () {
            success = false;
            errorResponse = {
                detail: 'email error'
            };
            spyOn($state, 'go');
            vm = createController();
            expect(utilities.storeData).toHaveBeenCalledWith('emailError', errorResponse.detail);
            expect($state.go).toHaveBeenCalledWith('web.permission-denied');
            expect(utilities.hideLoader).toHaveBeenCalled();
        });

        it('to load data with pagination `load` function', function () {
            success = true;
            successResponse = {

                next: 'page=4',
                previous: 'page=2',
            };
            vm = createController();
            spyOn(vm, 'startLoader');
            spyOn($http, 'get').and.callFake(function () {
                var deferred = $injector.get('$q').defer();
                return deferred.promise;
            });
            var url = 'participants/participant_team/page=2';
            vm.load(url);
            expect(vm.isExistLoader).toBeTruthy();
            expect(vm.startLoader).toHaveBeenCalledWith("Loading Teams");
            var headers = {
                'Authorization': "Token " + utilities.getData('userKey')
            };
            expect($http.get).toHaveBeenCalledWith(url, { headers: headers });
        });
    });

    describe('Unit tests for load function', function () {
        var $q, deferred;

        beforeEach(function () {
            $q = $injector.get('$q');
            deferred = $q.defer();
            success = true;
            successResponse = {
                next: 'page=4',
                previous: 'page=2',
                count: 15
            };
            vm = createController();
            spyOn(vm, 'startLoader');
            spyOn(vm, 'stopLoader');
        });

        it('should successfully load data and update pagination', function () {
            var url = 'hosts/challenge_host_team/?page=3';
            var mockResponse = {
                data: {
                    next: 'page=4',
                    previous: 'page=2',
                    count: 25,
                    results: [{ id: 1, team_name: 'Test Team' }]
                }
            };

            spyOn($http, 'get').and.returnValue($q.resolve(mockResponse));

            vm.load(url);
            $scope.$apply();

            expect(vm.startLoader).toHaveBeenCalledWith("Loading Teams");
            expect($http.get).toHaveBeenCalledWith(url, {
                headers: { 'Authorization': "Token " + utilities.getData('userKey') }
            });
            expect(vm.existTeam).toEqual(mockResponse.data);
            expect(vm.isNext).toEqual('');
            expect(vm.isPrev).toEqual('');
            expect(vm.currentPage).toEqual(3);
            expect(vm.stopLoader).toHaveBeenCalled();
        });

        it('should handle load function when next is null', function () {
            var url = 'hosts/challenge_host_team/?page=5';
            var mockResponse = {
                data: {
                    next: null,
                    previous: 'page=4',
                    count: 25,
                    results: [{ id: 1, team_name: 'Test Team' }]
                }
            };

            spyOn($http, 'get').and.returnValue($q.resolve(mockResponse));

            vm.load(url);
            $scope.$apply();

            expect(vm.existTeam).toEqual(mockResponse.data);
            expect(vm.isNext).toEqual('disabled');
            expect(vm.currentPage).toEqual(2.5); // count/10
            expect(vm.stopLoader).toHaveBeenCalled();
        });

        it('should handle load function when url is null', function () {
            vm.load(null);
            expect(vm.stopLoader).toHaveBeenCalled();
        });

        it('should handle HTTP error in load function', function () {
            var url = 'hosts/challenge_host_team/?page=3';
            spyOn($http, 'get').and.returnValue($q.reject({ data: { error: 'Network error' } }));

            vm.load(url);
            $scope.$apply();

            expect(vm.startLoader).toHaveBeenCalledWith("Loading Teams");
            expect(vm.stopLoader).toHaveBeenCalled();
        });
    });

    describe('Unit tests for showMdDialog function `hosts/challenge_host_team/<host_team_id>`', function () {
        var success;
        var successResponse = {
            team_name: "Team Name",
            team_url: "https://team.url"
        };
        var errorResponse = {
            error: 'error'
        };

        beforeEach(function () {
            spyOn($rootScope, 'notify');
            spyOn(vm, 'stopLoader');

            utilities.sendRequest = function (parameters) {
                if (success) {
                    parameters.callback.onSuccess({
                        data: successResponse
                    });
                } else {
                    parameters.callback.onError({
                        data: errorResponse
                    });
                }
            };
        });

        it('open dialog successfully', function () {
            success = true;
            var hostTeamId = 1;
            var ev = new Event('click');
            var $mdDialogOpened = false;
            $mdDialog.show = jasmine.createSpy().and.callFake(function () {
                $mdDialogOpened = true;
            });

            vm.showMdDialog(ev, hostTeamId);
            expect(vm.hostTeamId).toEqual(hostTeamId);
            expect(vm.team.TeamName).toEqual(successResponse.team_name);
            expect(vm.team.TeamURL).toEqual(successResponse.team_url);
            expect($mdDialog.show).toHaveBeenCalled();
            expect($mdDialogOpened).toBeTruthy();
        });

        it('backend error', function () {
            success = false;
            var hostTeamId = 1;
            var ev = new Event('click');
            var $mdDialogOpened = false;
            $mdDialog.show = jasmine.createSpy().and.callFake(function () {
                $mdDialogOpened = true;
            });

            vm.showMdDialog(ev, hostTeamId);
            expect(vm.hostTeamId).toEqual(hostTeamId);
            expect(vm.stopLoader).toHaveBeenCalled();
            expect($rootScope.notify).toHaveBeenCalledWith("error", errorResponse.error);
            expect($mdDialog.show).toHaveBeenCalled();
            expect($mdDialogOpened).toBeTruthy();
        });
    });

    describe('Unit tests for updateChallengeHostTeamData function', function () {
        var success, errorResponse = {};
        var successResponse = {
            results: {
                team_name: "Team Name",
                team_url: "https://team.url"
            }
        };

        beforeEach(function () {
            spyOn($rootScope, 'notify');
            spyOn(vm, 'stopLoader');
            spyOn($mdDialog, 'hide');

            utilities.sendRequest = function (parameters) {
                if (success) {
                    parameters.callback.onSuccess({
                        data: successResponse
                    });
                } else {
                    parameters.callback.onError({
                        data: errorResponse
                    });
                }
            };
        });

        it('successfully update the host team `hosts/challenge_host_team/<host_team_id>`', function () {
            success = true;
            var updateChallengeHostTeamDataForm = true;
            vm.team.TeamName = "Team Name";
            vm.team.TeamURL = "https://team.url";
            vm.updateChallengeHostTeamData(updateChallengeHostTeamDataForm);
            expect($mdDialog.hide).toHaveBeenCalled();
            expect($rootScope.notify).toHaveBeenCalledWith("success", "Host team updated!");
        });

        it('successfully retrive the updated list `hosts/challenge_host_team`', function () {
            success = true;
            var updateChallengeHostTeamDataForm = true;
            vm.updateChallengeHostTeamData(updateChallengeHostTeamDataForm);
            expect(vm.existTeam.results).toEqual(successResponse.results);
        });

        it('when team_name in response backend error `hosts/challenge_host_team/<host_team_id>`', function () {
            success = false;
            errorResponse.team_name = ["error in team name"];
            var updateChallengeHostTeamDataForm = true;
            vm.updateChallengeHostTeamData(updateChallengeHostTeamDataForm);
            expect($rootScope.notify).toHaveBeenCalledWith("error", errorResponse.team_name[0]);
        });

        it('when error in response backend error `hosts/challenge_host_team/<host_team_id>`', function () {
            success = false;
            errorResponse = {};
            errorResponse.error = ["error"];
            var updateChallengeHostTeamDataForm = true;
            vm.updateChallengeHostTeamData(updateChallengeHostTeamDataForm);
            expect($rootScope.notify).toHaveBeenCalledWith("error", errorResponse.error[0]);
        });

        it('invalid form submission', function () {
            var updateChallengeHostTeamDataForm = false;
            vm.updateChallengeHostTeamData(updateChallengeHostTeamDataForm);
            expect($mdDialog.hide).toHaveBeenCalled();
        });

        it('should reset team object after successful update', function () {
            success = true;
            var updateChallengeHostTeamDataForm = true;
            vm.team.TeamName = "Team Name";
            vm.team.TeamURL = "https://team.url";
            vm.updateChallengeHostTeamData(updateChallengeHostTeamDataForm);
            expect(vm.team).toEqual({});
        });

        it('should handle error when retrieving updated list fails', function () {
            success = false;
            errorResponse = { error: ['Failed to retrieve updated list'] };
            var updateChallengeHostTeamDataForm = true;
            
            // Mock the first call to succeed, second to fail
            var callCount = 0;
            utilities.sendRequest = function (parameters) {
                callCount++;
                if (callCount === 1) {
                    parameters.callback.onSuccess({ data: successResponse });
                } else {
                    parameters.callback.onError({ data: errorResponse });
                }
            };

            vm.updateChallengeHostTeamData(updateChallengeHostTeamDataForm);
            expect(vm.stopLoader).toHaveBeenCalled();
            expect($rootScope.notify).toHaveBeenCalledWith("error", errorResponse.error);
        });
    });

    describe('Unit tests for createNewTeam function `hosts/create_challenge_host_team`', function () {
        var success, successResponse;
        var hostTeamList = [
            {
                next: null,
                previous: null,
            },
            {
                next: null,
                previous: null,
            },
            {
                next: 'page=5',
                previous: null,
            },
            {
                next: null,
                previous: 'page=3',
            },
            {
                next: 'page=4',
                previous: 'page=2',
            }
        ];
        var errorResponse = {
            team_name: ['error']
        };

        beforeEach(function () {
            spyOn(vm, 'startLoader');
            spyOn(vm, 'stopLoader');
            spyOn(angular, 'element');
            spyOn($rootScope, 'notify');
            vm.team.name = "team_name";
            vm.team.url = "https://team.url";

            utilities.sendRequest = function (parameters) {
                if (success) {
                    parameters.callback.onSuccess({
                        data: successResponse,
                        status: 200
                    });
                } else {
                    parameters.callback.onError({
                        data: errorResponse
                    });
                }
            };
        });

        hostTeamList.forEach(response => {
            it('create new host team when pagination next is ' + response.next + 'and previous is ' + response.previous, function () {
                success = true;
                successResponse = response;

                vm.createNewTeam();
                expect(vm.isExistLoader).toEqual(true);
                expect(vm.loaderTitle).toEqual('');

                expect(vm.startLoader).toHaveBeenCalledWith("Loading Teams");
                expect($rootScope.notify).toHaveBeenCalled();
                expect(vm.stopLoader).toHaveBeenCalled();
                expect(vm.team).toEqual({});

                expect(vm.startLoader).toHaveBeenCalledWith("Loading Teams");
                expect(vm.existTeam).toEqual(successResponse);
                expect(vm.showPagination).toEqual(true);
                expect(vm.paginationMsg).toEqual('');

                if (vm.existTeam.next == null) {
                    expect(vm.isNext).toEqual('disabled');
                    expect(vm.currentPage).toEqual(1);
                } else {
                    expect(vm.isNext).toEqual('');
                    expect(vm.currentPage).toEqual(vm.existTeam.next.split('page=')[1] - 1);
                }

                if (vm.existTeam.previous == null) {
                    expect(vm.isPrev).toEqual('disabled');
                } else {
                    expect(vm.isPrev).toEqual('');
                }

                expect(vm.stopLoader).toHaveBeenCalled();
            });
        });

        it('backend error on creating new host team', function () {
            success = false;
            vm.createNewTeam();
            expect(vm.isExistLoader).toEqual(true);
            expect(vm.loaderTitle).toEqual('');
            expect(vm.startLoader("Loading Teams"));
            expect(vm.team.error).toEqual('error')
            expect(vm.stopLoader).toHaveBeenCalled();
            expect($rootScope.notify).toHaveBeenCalledWith("error", errorResponse.team_name[0]);
        });

        it('should handle error when refreshing team list after creation fails', function () {
            success = true;
            successResponse = { id: 1, team_name: 'New Team' };
            
            var callCount = 0;
            utilities.sendRequest = function (parameters) {
                callCount++;
                if (callCount === 1) {
                    parameters.callback.onSuccess({ data: successResponse, status: 200 });
                } else {
                    parameters.callback.onError({ data: { error: 'Failed to refresh' } });
                }
            };

            vm.createNewTeam();
            expect(vm.stopLoader).toHaveBeenCalled();
        });

        it('should set team error to false on successful creation', function () {
            success = true;
            successResponse = { id: 1, team_name: 'New Team' };
            vm.team.error = true; // Set initial error state
            
            vm.createNewTeam();
            expect(vm.team.error).toBeFalsy();
        });
    });

    describe('Unit tests for confirmDelete function', function () {
        beforeEach(function () {
            spyOn($mdDialog, 'show').and.callFake(function () {
                var deferred = $injector.get('$q').defer();
                return deferred.promise;
            });
        });

        it('open dialog to confirm delete', function () {
            var hostTeamId = 1;
            var ev = new Event('$click');
            var confirm = $mdDialog.confirm()
                .title('Would you like to remove yourself?')
                .textContent('Note: This action will remove you from the team.')
                .ariaLabel('Lucky day')
                .targetEvent(ev)
                .ok('Yes')
                .cancel("No");
            vm.confirmDelete(ev, hostTeamId);
            expect($mdDialog.show).toHaveBeenCalledWith(confirm);
        });

        it('should remove self from host team successfully and update team list', function (done) {
            var hostTeamId = 1;
            var ev = new Event('$click');

            $mdDialog.show.and.returnValue(Promise.resolve());

            spyOn(utilities, 'sendRequest').and.callFake(function (params) {
                if (params.method === 'DELETE') {
                    params.callback.onSuccess();
                } else if (params.method === 'GET') {
                    params.callback.onSuccess({
                        status: 200,
                        data: {
                            next: null,
                            previous: null,
                            count: 0
                        }
                    });
                }
            });
            spyOn(vm, 'startLoader').and.callThrough();
            spyOn(vm, 'stopLoader').and.callThrough();
            spyOn($rootScope, 'notify');
            vm.confirmDelete(ev, hostTeamId);
            setTimeout(function () {
                expect($mdDialog.show).toHaveBeenCalled();
                expect(vm.startLoader).toHaveBeenCalled();
                expect(utilities.sendRequest).toHaveBeenCalled();
                expect($rootScope.notify).toHaveBeenCalledWith("info", "You have removed yourself successfully");
                expect(vm.existTeam.count).toBe(0);
                expect(vm.showPagination).toBe(false);
                expect(vm.paginationMsg).toBe("No team exists for now, start by creating a new team!");
                expect(vm.stopLoader).toHaveBeenCalled();
                done();
            }, 0);
        });

        it('should show error notification if remove self from host team fails', function (done) {
            var hostTeamId = 1;
            var ev = new Event('$click');
            $mdDialog.show.and.returnValue(Promise.resolve());
            spyOn(vm, 'startLoader').and.callThrough();
            spyOn(vm, 'stopLoader').and.callThrough();
            spyOn($rootScope, 'notify');
            spyOn(utilities, 'sendRequest').and.callFake(function (params) {
                if (params.method === 'DELETE') {
                    params.callback.onError();
                }
            });
            vm.confirmDelete(ev, hostTeamId);
            setTimeout(function () {
                expect(vm.startLoader).toHaveBeenCalled();
                expect($rootScope.notify).toHaveBeenCalledWith("error", "Couldn't remove you from the challenge");
                expect(vm.stopLoader).toHaveBeenCalled();
                done();
            }, 0);
        });

        it('should do nothing if dialog is cancelled', function (done) {
            var hostTeamId = 1;
            var ev = new Event('$click');
            $mdDialog.show.and.returnValue(Promise.reject());
            spyOn(vm, 'startLoader');
            spyOn(utilities, 'sendRequest');
            vm.confirmDelete(ev, hostTeamId);
            setTimeout(function () {
                expect(vm.startLoader).not.toHaveBeenCalled();
                expect(utilities.sendRequest).not.toHaveBeenCalled();
                done();
            }, 0);
        });

        it('should handle pagination correctly after successful deletion with remaining teams', function (done) {
            var hostTeamId = 1;
            var ev = new Event('$click');

            $mdDialog.show.and.returnValue(Promise.resolve());

            spyOn(utilities, 'sendRequest').and.callFake(function (params) {
                if (params.method === 'DELETE') {
                    params.callback.onSuccess();
                } else if (params.method === 'GET') {
                    params.callback.onSuccess({
                        status: 200,
                        data: {
                            next: 'page=3',
                            previous: 'page=1',
                            count: 15,
                            results: [{ id: 2, team_name: 'Remaining Team' }]
                        }
                    });
                }
            });
            spyOn(vm, 'startLoader').and.callThrough();
            spyOn(vm, 'stopLoader').and.callThrough();
            spyOn($rootScope, 'notify');

            vm.confirmDelete(ev, hostTeamId);
            setTimeout(function () {
                expect(vm.existTeam.count).toBe(15);
                expect(vm.showPagination).toBe(true);
                expect(vm.paginationMsg).toBe("");
                expect(vm.isNext).toBe('');
                expect(vm.isPrev).toBe('');
                expect(vm.currentPage).toBe(2); // page=3 - 1
                done();
            }, 0);
        });

        it('should stop propagation of click event', function () {
            var hostTeamId = 1;
            var ev = {
                stopPropagation: jasmine.createSpy('stopPropagation')
            };
            
            vm.confirmDelete(ev, hostTeamId);
            expect(ev.stopPropagation).toHaveBeenCalled();
        });
    });

    describe('Unit tests for inviteOthers function', function () {
        beforeEach(function () {
            spyOn($mdDialog, 'show').and.callFake(function () {
                var deferred = $injector.get('$q').defer();
                return deferred.promise;
            });
        });

        it('open dialog to invite others', function () {
            var hostId = 1;
            var ev = new Event('$click');
            var confirm = $mdDialog.prompt()
                .title('Add other members to your team')
                .textContent('Enter the email address of the person')
                .placeholder('email')
                .ariaLabel('')
                .targetEvent(ev)
                .ok('Add')
                .cancel('Cancel');
            vm.inviteOthers(ev, hostId);
            expect($mdDialog.show).toHaveBeenCalledWith(confirm);
        });

        it('should successfully invite user when dialog is confirmed', function (done) {
            var hostTeamId = 1;
            var ev = new Event('$click');
            var email = 'test@example.com';
            
            $mdDialog.show.and.returnValue(Promise.resolve(email));
            
            spyOn(utilities, 'sendRequest').and.callFake(function (params) {
                expect(params.url).toBe('hosts/challenge_host_teams/' + hostTeamId + '/invite');
                expect(params.method).toBe('POST');
                expect(params.data.email).toBe(email);
                expect(params.token).toBe(utilities.getData('userKey'));
                
                
                params.callback.onSuccess();
            });
            
            spyOn($rootScope, 'notify');
            
            vm.inviteOthers(ev, hostTeamId);
            
            setTimeout(function () {
                expect(utilities.sendRequest).toHaveBeenCalled();
                expect($rootScope.notify).toHaveBeenCalledWith("success", email + " has been added successfully");
                done();
            }, 0);
        });
    
        it('should show error notification when invitation fails', function (done) {
            var hostTeamId = 1;
            var ev = new Event('$click');
            var email = 'test@example.com';
            var errorMessage = 'User not found';
            
            $mdDialog.show.and.returnValue(Promise.resolve(email));
            
            spyOn(utilities, 'sendRequest').and.callFake(function (params) {
                expect(params.url).toBe('hosts/challenge_host_teams/' + hostTeamId + '/invite');
                expect(params.method).toBe('POST');
                expect(params.data.email).toBe(email);
                expect(params.token).toBe(utilities.getData('userKey'));
                
                
                params.callback.onError({
                    data: {
                        error: errorMessage
                    }
                });
            });
            
            spyOn($rootScope, 'notify');
            
            vm.inviteOthers(ev, hostTeamId);
            
            setTimeout(function () {
                expect(utilities.sendRequest).toHaveBeenCalled();
                expect($rootScope.notify).toHaveBeenCalledWith("error", errorMessage);
                done();
            }, 0);
        });

        it('should stop propagation of click event', function () {
            var hostTeamId = 1;
            var ev = {
                stopPropagation: jasmine.createSpy('stopPropagation')
            };
            
            vm.inviteOthers(ev, hostTeamId);
            expect(ev.stopPropagation).toHaveBeenCalled();
        });

        it('should handle dialog cancellation gracefully', function (done) {
            var hostTeamId = 1;
            var ev = new Event('$click');
            
            $mdDialog.show.and.returnValue(Promise.reject());
            spyOn(utilities, 'sendRequest');
            
            vm.inviteOthers(ev, hostTeamId);
            
            setTimeout(function () {
                expect(utilities.sendRequest).not.toHaveBeenCalled();
                done();
            }, 0);
        });

        it('should handle invitation of existing team member', function (done) {
            var hostTeamId = 1;
            var ev = new Event('$click');
            var email = 'existing@example.com';
            var errorMessage = 'User is already a member of this team';
            
            $mdDialog.show.and.returnValue(Promise.resolve(email));
            
            spyOn(utilities, 'sendRequest').and.callFake(function (params) {
                params.callback.onError({
                    data: {
                        error: errorMessage
                    }
                });
            });
            
            spyOn($rootScope, 'notify');
            
            vm.inviteOthers(ev, hostTeamId);
            
            setTimeout(function () {
                expect($rootScope.notify).toHaveBeenCalledWith("error", errorMessage);
                done();
            }, 0);
        });
    });

    describe('Unit tests for storeChallengeHostTeamId function', function () {
        beforeEach(function () {
            spyOn(utilities, 'storeData');
            spyOn($state, 'go');
        });

        it('store challenge host team ID', function () {
            vm.challengeHostTeamId = 1;
            vm.storeChallengeHostTeamId();
            expect(utilities.storeData).toHaveBeenCalledWith('challengeHostTeamId', vm.challengeHostTeamId);
            expect($state.go).toHaveBeenCalledWith('web.challenge-create');
        });

        it('should handle null challengeHostTeamId', function () {
            vm.challengeHostTeamId = null;
            vm.storeChallengeHostTeamId();
            expect(utilities.storeData).toHaveBeenCalledWith('challengeHostTeamId', null);
            expect($state.go).toHaveBeenCalledWith('web.challenge-create');
        });

        it('should handle undefined challengeHostTeamId', function () {
            vm.challengeHostTeamId = undefined;
            vm.storeChallengeHostTeamId();
            expect(utilities.storeData).toHaveBeenCalledWith('challengeHostTeamId', undefined);
            expect($state.go).toHaveBeenCalledWith('web.challenge-create');
        });
    });

    describe('Additional edge case tests', function () {
        it('should handle loaderContainer assignment correctly', function () {
            vm = createController();
            var mockElement = { addClass: jasmine.createSpy() };
            spyOn(angular, 'element').and.returnValue(mockElement);
            
            expect(vm.loaderContainer).toBeDefined();
            expect(angular.element).toHaveBeenCalledWith('.exist-team-card');
        });

        it('should handle team object initialization', function () {
            vm = createController();
            expect(vm.team).toBeDefined();
            expect(typeof vm.team).toBe('object');
        });

        it('should handle initial pagination state correctly', function () {
            var success = true;
            var successResponse = {
                count: 5,
                next: null,
                previous: null,
                results: [
                    { id: 1, team_name: 'Team 1' },
                    { id: 2, team_name: 'Team 2' }
                ]
            };

            spyOn(utilities, 'deleteData');
            spyOn(utilities, 'hideLoader');

            utilities.sendRequest = function (parameters) {
                parameters.callback.onSuccess({
                    data: successResponse,
                    status: 200
                });
            };

            vm = createController();
            expect(vm.showPagination).toBeTruthy();
            expect(vm.isNext).toEqual('disabled');
            expect(vm.isPrev).toEqual('disabled');
            expect(vm.currentPage).toEqual(1);
        });
    });
});