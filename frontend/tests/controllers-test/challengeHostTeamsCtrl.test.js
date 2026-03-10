'use strict';

describe('Unit tests for challenge host team controller', function () {
    beforeEach(angular.mock.module('evalai'));

    var $controller, createController, $injector, $mdDialog, $rootScope, $state, $scope, loaderService, utilities, $http, $compile, vm;

    beforeEach(inject(function (_$controller_, _$injector_, _$mdDialog_, _$rootScope_, _$state_, _utilities_, _loaderService_, _$http_, _$compile_) {
        $controller = _$controller_;
        $injector = _$injector_;
        $rootScope = _$rootScope_;
        $state = _$state_;
        utilities = _utilities_;
        loaderService = _loaderService_;
        $http = _$http_;
        $mdDialog = _$mdDialog_;
        $compile = _$compile_;

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

        it('should initialize loaderContainer correctly', function () {
            spyOn(angular, 'element').and.returnValue('mocked-element');
            vm = createController();
            expect(angular.element).toHaveBeenCalledWith('.exist-team-card');
            expect(vm.loaderContainer).toEqual('mocked-element');
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

        it('should test activateCollapsible function', function () {
            spyOn(angular, 'element').and.returnValue({
                collapsible: jasmine.createSpy('collapsible')
            });
            vm = createController();
            vm.activateCollapsible();
            expect(angular.element).toHaveBeenCalledWith('.collapsible');
            expect(angular.element('.collapsible').collapsible).toHaveBeenCalled();
        });
    });

    describe('Unit tests for global backend calls', function () {
        var success, successResponse, errorResponse;
        var hostTeamList = [
            {
                next: null,
                previous: null,
                count: 0
            },
            {
                next: null,
                previous: null,
                count: 5
            },
            {
                next: 'page=5',
                previous: null,
                count: 50
            },
            {
                next: null,
                previous: 'page=3',
                count: 30
            },
            {
                next: 'page=4',
                previous: 'page=2',
                count: 40
            }
        ];

        beforeEach(function () {
            spyOn(utilities, 'deleteData');
            spyOn(utilities, 'storeData');
            spyOn(utilities, 'hideLoader');
            spyOn(angular, 'element').and.returnValue({
                collapsible: jasmine.createSpy('collapsible')
            });

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
            it('when pagination next is ' + response.next + ' and previous is ' + response.previous + ' and count is ' + response.count + ' `hosts/challenge_host_team/`', function () {
                success = true;
                successResponse = response;
                vm = createController();
                expect(vm.existTeam).toEqual(successResponse);
                
                if (vm.existTeam.count === 0) {
                    expect(vm.showPagination).toBeFalsy();
                    expect(vm.paginationMsg).toEqual("No team exists for now. Start by creating a new team!");
                } else {
                    expect(vm.showPagination).toBeTruthy();
                    expect(vm.paginationMsg).toEqual('');
                    expect(angular.element('.collapsible').collapsible).toHaveBeenCalled();
                }
                
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

        it('to load data with pagination `load` function with valid URL', function () {
            success = true;
            successResponse = {
                next: 'page=4',
                previous: 'page=2',
                count: 30
            };
            vm = createController();
            spyOn(vm, 'startLoader');
            spyOn(vm, 'stopLoader');
            
            var mockResponse = {
                data: successResponse
            };
            
            spyOn($http, 'get').and.callFake(function () {
                var deferred = $injector.get('$q').defer();
                deferred.resolve(mockResponse);
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
            
            // Trigger the promise resolution
            $scope.$apply();
            
            expect(vm.existTeam).toEqual(successResponse);
            expect(vm.stopLoader).toHaveBeenCalled();
        });

        it('to load data with pagination `load` function with null URL', function () {
            success = true;
            successResponse = {
                next: 'page=4',
                previous: 'page=2',
            };
            vm = createController();
            spyOn(vm, 'startLoader');
            spyOn(vm, 'stopLoader');
            spyOn($http, 'get');
            
            vm.load(null);
            expect(vm.isExistLoader).toBeTruthy();
            expect(vm.startLoader).toHaveBeenCalledWith("Loading Teams");
            expect($http.get).not.toHaveBeenCalled();
            expect(vm.stopLoader).toHaveBeenCalled();
        });

        it('should handle pagination when next is null and calculate currentPage from count', function () {
            success = true;
            successResponse = {
                next: null,
                previous: 'page=2',
                count: 25
            };
            vm = createController();
            spyOn(vm, 'startLoader');
            spyOn(vm, 'stopLoader');
            
            var mockResponse = {
                data: successResponse
            };
            
            spyOn($http, 'get').and.callFake(function () {
                var deferred = $injector.get('$q').defer();
                deferred.resolve(mockResponse);
                return deferred.promise;
            });
            
            var url = 'participants/participant_team/page=3';
            vm.load(url);
            
            // Trigger the promise resolution
            $scope.$apply();
            
            expect(vm.existTeam).toEqual(successResponse);
            expect(vm.isNext).toEqual('disabled');
            expect(vm.currentPage).toEqual(vm.existTeam.count / 10);
            expect(vm.isPrev).toEqual('');
        });

        it('should handle pagination when next is not null and calculate currentPage correctly', function () {
            success = true;
            successResponse = {
                next: 'page=5',
                previous: 'page=3',
                count: 45
            };
            vm = createController();
            spyOn(vm, 'startLoader');
            spyOn(vm, 'stopLoader');
            
            var mockResponse = {
                data: successResponse
            };
            
            spyOn($http, 'get').and.callFake(function () {
                var deferred = $injector.get('$q').defer();
                deferred.resolve(mockResponse);
                return deferred.promise;
            });
            
            var url = 'participants/participant_team/page=4';
            vm.load(url);
            
            // Trigger the promise resolution
            $scope.$apply();
            
            expect(vm.existTeam).toEqual(successResponse);
            expect(vm.isNext).toEqual('');
            expect(vm.currentPage).toEqual(parseInt(vm.existTeam.next.split('page=')[1] - 1));
            expect(vm.isPrev).toEqual('');
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

        it('should handle error in retrieving updated list after successful update', function () {
            var callCount = 0;
            utilities.sendRequest = function (parameters) {
                callCount++;
                if (callCount === 1) {
                    // First call (update) succeeds
                    parameters.callback.onSuccess({
                        data: successResponse
                    });
                } else {
                    // Second call (get updated list) fails
                    parameters.callback.onError({
                        data: { error: 'Failed to retrieve updated list' }
                    });
                }
            };

            var updateChallengeHostTeamDataForm = true;
            vm.team.TeamName = "Team Name";
            vm.team.TeamURL = "https://team.url";
            vm.updateChallengeHostTeamData(updateChallengeHostTeamDataForm);
            
            expect($mdDialog.hide).toHaveBeenCalled();
            expect($rootScope.notify).toHaveBeenCalledWith("success", "Host team updated!");
            expect(vm.stopLoader).toHaveBeenCalled();
            expect($rootScope.notify).toHaveBeenCalledWith("error", 'Failed to retrieve updated list');
        });
    });

    describe('Unit tests for createNewTeam function `hosts/create_challenge_host_team`', function () {
        var success, successResponse;
        var hostTeamList = [
            {
                next: null,
                previous: null,
                count: 1
            },
            {
                next: null,
                previous: null,
                count: 5
            },
            {
                next: 'page=5',
                previous: null,
                count: 50
            },
            {
                next: null,
                previous: 'page=3',
                count: 30
            },
            {
                next: 'page=4',
                previous: 'page=2',
                count: 40
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
            it('create new host team when pagination next is ' + response.next + ' and previous is ' + response.previous + ' and count is ' + response.count, function () {
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

        it('should handle error in retrieving updated list after successful team creation', function () {
            var callCount = 0;
            utilities.sendRequest = function (parameters) {
                callCount++;
                if (callCount === 1) {
                    // First call (create team) succeeds
                    parameters.callback.onSuccess({
                        data: { id: 123, team_name: 'New Team' },
                        status: 200
                    });
                } else {
                    // Second call (get updated list) fails
                    parameters.callback.onError({
                        data: { error: 'Failed to retrieve teams' }
                    });
                }
            };

            vm.createNewTeam();
            expect(vm.stopLoader).toHaveBeenCalled();
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
            spyOn(ev, 'stopPropagation');
            var confirm = $mdDialog.confirm()
                .title('Would you like to remove yourself?')
                .textContent('Note: This action will remove you from the team.')
                .ariaLabel('Lucky day')
                .targetEvent(ev)
                .ok('Yes')
                .cancel("No");
            vm.confirmDelete(ev, hostTeamId);
            expect(ev.stopPropagation).toHaveBeenCalled();
            expect($mdDialog.show).toHaveBeenCalledWith(confirm);
        });

        it('should remove self from host team successfully and update team list', function (done) {
            var hostTeamId = 1;
            var ev = new Event('$click');
            spyOn(ev, 'stopPropagation');

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
            spyOn(ev, 'stopPropagation');
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
            spyOn(ev, 'stopPropagation');
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

        it('should handle successful removal with teams remaining', function (done) {
            var hostTeamId = 1;
            var ev = new Event('$click');
            spyOn(ev, 'stopPropagation');

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
                            count: 15
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
                expect(vm.currentPage).toBe(parseInt(vm.existTeam.next.split('page=')[1] - 1));
                done();
            }, 0);
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
            spyOn(ev, 'stopPropagation');
            var confirm = $mdDialog.prompt()
                .title('Add other members to your team')
                .textContent('Enter the email address of the person')
                .placeholder('email')
                .ariaLabel('')
                .targetEvent(ev)
                .ok('Add')
                .cancel('Cancel');
            vm.inviteOthers(ev, hostId);
            expect(ev.stopPropagation).toHaveBeenCalled();
            expect($mdDialog.show).toHaveBeenCalledWith(confirm);
        });

        it('should successfully invite user when dialog is confirmed', function (done) {
            var hostTeamId = 1;
            var ev = new Event('$click');
            spyOn(ev, 'stopPropagation');
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
            spyOn(ev, 'stopPropagation');
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

        it('should do nothing if dialog is cancelled', function (done) {
            var hostTeamId = 1;
            var ev = new Event('$click');
            spyOn(ev, 'stopPropagation');
            
            $mdDialog.show.and.returnValue(Promise.reject());
            spyOn(utilities, 'sendRequest');
            
            vm.inviteOthers(ev, hostTeamId);
            
            setTimeout(function () {
                expect(utilities.sendRequest).not.toHaveBeenCalled();
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

        it('store challenge host team ID with different value', function () {
            vm.challengeHostTeamId = 999;
            vm.storeChallengeHostTeamId();
            expect(utilities.storeData).toHaveBeenCalledWith('challengeHostTeamId', 999);
            expect($state.go).toHaveBeenCalledWith('web.challenge-create');
        });
    });
});