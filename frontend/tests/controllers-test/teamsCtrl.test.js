'use strict';

describe('Unit tests for teams controller', function () {
    beforeEach(angular.mock.module('evalai'));

    var $controller, createController, $injector, $rootScope, $scope, utilities, $mdDialog, $state, $http, vm;

    beforeEach(inject(function (_$controller_, _$rootScope_, _$injector_, _utilities_, _$mdDialog_, _loaderService_, _$state_, _$http_, ) {
        $controller = _$controller_;
        $rootScope = _$rootScope_;
        utilities = _utilities_;
        $mdDialog = _$mdDialog_;
        $state =_$state_;
        $http = _$http_;
        $injector = _$injector_;

        $scope = $rootScope.$new();
        createController = function () {
            return $controller('TeamsCtrl', {$scope: $scope});
        };
        vm = $controller('TeamsCtrl', { $scope: $scope });
    }));

    describe('Global variables', function () {
        it('has default values', function () {
            spyOn(utilities, 'showLoader');
            spyOn(utilities, 'getData');
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
            expect(vm.isExistLoader).toBeFalsy();
            expect(vm.loaderTitle).toEqual('');
        });
    });

    describe('Unit tests for global backend calls', function () {
        var success, successResponse, errorResponse;
        var teamList = [
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

        teamList.forEach(response => {
            it('when pagination next is ' + response.next + 'and previous is ' + response.previous + '\
            `participants/participant_team`', function () {
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

        it('success of selectExistTeam function \
        `challenges/challenge/<challenge_id>/participant_team/<team_id>`', function () {
            success = true;
            successResponse = {
                next: 'page=4',
                previous: 'page=2',
            };
            vm = createController();
            spyOn(vm, 'startLoader');
            spyOn(vm, 'stopLoader');
            spyOn($state, 'go');
            spyOn(angular, 'element');
            vm.selectExistTeam();
            expect(vm.loaderTitle).toEqual('');
            expect(angular.element).toHaveBeenCalledWith('.exist-team-card');
            expect(vm.startLoader).toHaveBeenCalledWith("Loading Teams");
            expect($state.go).toHaveBeenCalledWith('web.challenge-page.overview');
            expect(vm.stopLoader).toHaveBeenCalled();
        });

        it('backend error of selectExistTeam function \
        `challenges/challenge/<challenge_id>/participant_team/<team_id>`', function () {
            success = true;
            // team pagination response
            successResponse = {
                next: 'page=4',
                previous: 'page=2',
            };
            errorResponse = {
                next: 'page=4',
                previous: 'page=2',
            };
            vm = createController();
            success = false;
            spyOn(vm, 'startLoader');
            spyOn(vm, 'stopLoader');
            spyOn($state, 'go');
            spyOn(angular, 'element');

            vm.selectExistTeam();
            expect(vm.loaderTitle).toEqual('');
            expect(angular.element).toHaveBeenCalledWith('.exist-team-card');
            expect(vm.startLoader).toHaveBeenCalledWith("Loading Teams");
            expect(vm.existTeamError).toEqual("Please select a team");
            expect(vm.stopLoader).toHaveBeenCalled();
        });

        it('to load data with pagination `load` function', function () {
            success = true;
            successResponse = {
                // team pagination response
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

        it('backend error for the global function \
        `participants/participant_team`', function () {
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
    });

    describe('Unit tests for createNewTeam function', function () {
        var success, successResponse;
        var errorResponse = {
            team_name: ['error']
        };
        var teamList = [
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
            vm = createController();
            spyOn(vm, 'startLoader');
            spyOn(vm, 'stopLoader');
            spyOn($rootScope, 'notify');
            spyOn(angular, 'element');

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

        teamList.forEach(response => {
            it('when pagination next is ' + response.next + 'and previous is ' + response.previous + '\
            `participants/participant_team`', function () {;
                success = true;
                successResponse = response;
                vm.team.teamName = "Team Name";
                vm.team.teamUrl = "https://team.url";
                vm.createNewTeam();
                expect(vm.isExistLoader).toBeTruthy();
                expect(vm.loaderTitle).toEqual('');
                expect(angular.element).toHaveBeenCalledWith('.new-team-card');
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

        it('backend error of the createNewTeam function `participants/participant_team`', function () {
            success = false;
            vm.createNewTeam();
            expect(vm.isExistLoader).toBeTruthy();
            expect(vm.loaderTitle).toEqual('');
            expect(angular.element).toHaveBeenCalledWith('.new-team-card');
            expect(vm.startLoader("Loading Teams"));
            expect(vm.team.error).toEqual(errorResponse.team_name[0]);
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
            var participantTeamId = 1;
            var ev = new Event('$click');
            var confirm = $mdDialog.confirm()
                .title('Would you like to remove yourself?')
                .textContent('Note: This action will remove you from the team.')
                .ariaLabel('Lucky day')
                .targetEvent(ev)
                .ok('Yes')
                .cancel("No");
            vm.confirmDelete(ev, participantTeamId);
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
            var participantTeamId = 1;
            var ev = new Event('$click');
            var confirm = $mdDialog.prompt()
                .title('Add other members to this Team')
                .textContent('Enter the email address of the person')
                .placeholder('email')
                .ariaLabel('')
                .targetEvent(ev)
                .ok('Add')
                .cancel('Cancel');
            vm.inviteOthers(ev, participantTeamId);
            expect($mdDialog.show).toHaveBeenCalledWith(confirm);
        });
    });

    describe('Unit tests for showMdDialog function `participants/participant_team/`', function () {
        var success;
        var successResponse = {
            team_name: "Team Name",
            team_url: "https://team.url"
        }
        var errorResponse = {
            error: 'error'
        };

        beforeEach(function () {
            spyOn(vm, 'stopLoader');
            spyOn($rootScope, 'notify');

            utilities.sendRequest = function (parameters) {
                if (success) {
                    parameters.callback.onSuccess({
                        data: successResponse,
                    });
                } else {
                    parameters.callback.onError({
                        data: errorResponse
                    });
                }
            };
        });

        it('successfully get the team details', function () {
            success = true;
            var participantTeamId = 1;
            var ev = new Event('click');
            vm.showMdDialog(ev, participantTeamId);
            expect(vm.participantTeamId).toEqual(participantTeamId);
            expect(vm.team.teamName).toEqual(successResponse.team_name);
            expect(vm.team.teamUrl).toEqual(successResponse.team_url);
        });

        it('backend error', function () {
            success = false;
            var participantTeamId = 1;
            var ev = new Event('click');
            vm.showMdDialog(ev, participantTeamId);
            expect(vm.stopLoader).toHaveBeenCalled();
            expect($rootScope.notify).toHaveBeenCalledWith("error", errorResponse['error']);
        });

        it('show dialog', function () {
            var $mdDialogOpened = false;
            $mdDialog.show = jasmine.createSpy().and.callFake(function () {
                $mdDialogOpened = true;
            });
            var participantTeamId = 1;
            var ev = new Event('click');

            vm.showMdDialog(ev, participantTeamId);
            expect($mdDialog.show).toHaveBeenCalled();
            expect($mdDialogOpened).toBe(true);
        });
    });

    describe('Unit tests for updateParticipantTeamData `participants/participant_team/<participant_team_id>`', function () {
        var success, successResponse, errorResponse;
        var successResponse = {
            results: {
                team_name: "Team Name",
                team_url: "https://team.url",
                created_by: "user"
            }
        }

        beforeEach(function () {
            spyOn(vm, 'stopLoader');
            spyOn($rootScope, 'notify');
            spyOn($mdDialog, 'hide');
            vm.team.name = "Team Name";
            vm.team.url = "https://team.url";

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

        it('successfully updated participant team data', function () {
            var updateParticipantTeamDataForm = true;
            success = true;
            vm.updateParticipantTeamData(updateParticipantTeamDataForm);
            expect($mdDialog.hide).toHaveBeenCalled();
            expect(vm.team).toEqual({});
            expect($rootScope.notify).toHaveBeenCalledWith("success", "Participant Team updated!");
        });

        it('retrieves the updated lists', function () {
            var updateParticipantTeamDataForm = true;
            success = true;
            vm.updateParticipantTeamData(updateParticipantTeamDataForm);
            expect(vm.existTeam.results).toEqual(successResponse.results);
        });

        it('error when `team_name` in response', function () {
            var updateParticipantTeamDataForm = true;
            success = false;
            errorResponse = {
                team_name:['team name error'],
                error: ['error']	
            };
            vm.updateParticipantTeamData(updateParticipantTeamDataForm);
            expect($rootScope.notify).toHaveBeenCalledWith("error", errorResponse.team_name[0]);
        });

        it('other backend error', function () {
            var updateParticipantTeamDataForm = true;
            success = false;
            errorResponse = {
                error: ['error']	
            };
            vm.updateParticipantTeamData(updateParticipantTeamDataForm);
            expect($rootScope.notify).toHaveBeenCalledWith("error", errorResponse.error[0]);
        });

        it('invalid form submission', function () {
            var updateParticipantTeamDataForm = false;
            vm.updateParticipantTeamData(updateParticipantTeamDataForm);
            expect($mdDialog.hide).toHaveBeenCalled();
        });
    });
});
