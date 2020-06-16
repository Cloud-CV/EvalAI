'use strict';

describe('Unit tests for challenge host team controller', function () {
    beforeEach(angular.mock.module('evalai'));

    var $controller, createController, $injector, $mdDialog, $rootScope, $state, $scope, loaderService, utilities,$http, $compile, vm;

    beforeEach(inject(function (_$controller_, _$injector_, _$mdDialog_,  _$rootScope_, _$state_, _utilities_, _loaderService_, _$http_, _$compile_) {
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
            return $controller('ChallengeHostTeamsCtrl', {$scope: $scope});
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
            `hosts/challenge_host_team/`', function () {;
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
                // host team pagination response
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
            expect($http.get).toHaveBeenCalledWith(url, {headers: headers});
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
    });

    describe('Unit tests for storeChallengeHostTeamId function', function () {
        beforeEach(function (){
            spyOn(utilities, 'storeData');
            spyOn($state, 'go');
        });

        it('store challenge host team ID', function () {
            vm.challengeHostTeamId = 1;
            vm.storeChallengeHostTeamId();
            expect(utilities.storeData).toHaveBeenCalledWith('challengeHostTeamId', vm.challengeHostTeamId);
            expect($state.go).toHaveBeenCalledWith('web.challenge-create');
        });
    });
});
