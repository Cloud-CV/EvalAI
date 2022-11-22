'use strict';

describe('Unit tests for dashboard controller', function () {
    beforeEach(angular.mock.module('evalai'));

    var $controller, createController, $rootScope, $state, $scope, utilities, vm;

    beforeEach(inject(function (_$controller_, _$state_, _$rootScope_,  _utilities_,) {
        $controller = _$controller_;
        $rootScope = _$rootScope_;
        utilities = _utilities_;
        $state = _$state_;

        $scope = $rootScope.$new();
        createController = function () {
            return $controller('DashCtrl', {$scope: $scope});
        };
        vm = $controller('DashCtrl', { $scope: $scope });
    }));

    describe('Global variables', function () {
        it('has default values', function () {
            utilities.storeData('userKey', 'encrypted key');
            spyOn(utilities, 'getData');
            vm = createController();

            expect(vm.challengeCount).toEqual(0);
            expect(vm.hostTeamCount).toEqual(0);
            expect(vm.hostTeamExist).toBeFalsy();
            expect(vm.participatedTeamCount).toEqual(0);
            expect(utilities.getData).toHaveBeenCalledWith('userKey');
            expect(vm.redirectUrl).toEqual({});
        });
    });

    describe('Unit tests for global backend calls', function () {
        var successResponse, errorResponse, status;
        var isUserDetails, isPresentChallenge, isHostTeam, isParticipantTeam;

        beforeEach(function () {
            spyOn(utilities, 'resetStorage');
            spyOn($state, 'go');
            spyOn(window, 'alert');

            utilities.sendRequest = function (parameters) {
                if ((isUserDetails == true && parameters.url == 'auth/user/') ||
                (isPresentChallenge == true && parameters.url == 'challenges/challenge/present/approved/public') ||
                (isHostTeam == true && parameters.url == 'hosts/challenge_host_team/') ||
                (isParticipantTeam == true && parameters.url == 'participants/participant_team')) {
                    parameters.callback.onSuccess({
                        data: successResponse,
                        status: 200
                    });
                } else if ((isUserDetails == false && parameters.url == 'auth/user/') ||
                (isPresentChallenge == false && parameters.url == 'challenges/challenge/present/approved/public') ||
                (isHostTeam == false && parameters.url == 'hosts/challenge_host_team/') ||
                (isParticipantTeam == false && parameters.url == 'participants/participant_team')){
                    parameters.callback.onError({
                        data: errorResponse,
                        status: status
                    });
                }
            };
        });

        it('get the user details `auth/user/`', function () {
            isUserDetails = true;
            isPresentChallenge = null;
            isHostTeam = null;
            isParticipantTeam = null;
            successResponse = {
                username: 'xyz',
                first_name: 'first name',
                last_name: 'last name'
            };
            vm = createController();
            expect(vm.name).toEqual(successResponse.username);

        });

        it('403 backend error on getting user details `auth/user/`', function () {
            isUserDetails = false;
            isPresentChallenge = null;
            isHostTeam = null;
            isParticipantTeam = null;
            status = 403;
            errorResponse = {
                error: 'error'
            };
            vm = createController();
            expect(vm.error).toEqual(errorResponse);
            expect(vm.isPrivileged).toEqual(false);
        });

        it('401 backend error on getting user details `auth/user/`', function () {
            isUserDetails = false;
            isPresentChallenge = null;
            isHostTeam = null;
            isParticipantTeam = null;
            status = 401;
            errorResponse = {
                error: 'error'
            };
            vm = createController();
            expect(window.alert).toHaveBeenCalledWith("Timeout, Please login again to continue!");
            expect(utilities.resetStorage).toHaveBeenCalled();
            expect($state.go).toHaveBeenCalledWith("auth.login");
            expect($rootScope.isAuth).toBeFalsy();
        });

        it('get all ongoing challenges `challenges/challenge/present/approved/public`', function () {
            isUserDetails = null;
            isPresentChallenge = true;
            isHostTeam = null;
            isParticipantTeam = null;
            successResponse = {
                results: [
                    {
                        id: 1,
                        title: "Challenge title 1",
                        description: "Challenge description 1"
                    },
                    {
                        id: 2,
                        title: "Challenge title 2",
                        description: "Challenge description 2"
                    },
                ]
            };
            vm = createController();
            expect(vm.challengeCount).toEqual(successResponse.results.length);
            expect(vm.hostTeamExist).toBeFalsy();
        });

        it('403 backend error on getting all ongoing challenges `challenges/challenge/present/approved/public`', function () {
            isUserDetails = null;
            isPresentChallenge = false;
            isHostTeam = null;
            isParticipantTeam = null;
            status = 403;
            errorResponse = {
                error: 'error'
            };
            vm = createController();
            expect(vm.error).toEqual(errorResponse);
            expect(vm.isPrivileged).toEqual(false);
        });

        it('401 backend error on getting all ongoing challenges `challenges/challenge/present/approved/public`', function () {
            isUserDetails = null;
            isPresentChallenge = false;
            isHostTeam = null;
            isParticipantTeam = null;
            status = 401;
            errorResponse = {
                error: 'error'
            };
            vm = createController();
            expect(window.alert).toHaveBeenCalledWith("Timeout, Please login again to continue!");
            expect(utilities.resetStorage).toHaveBeenCalled();
            expect($state.go).toHaveBeenCalledWith("auth.login");
            expect($rootScope.isAuth).toBeFalsy();
        });

        it('get host teams details `hosts/challenge_host_team/`', function () {
            isUserDetails = null;
            isPresentChallenge = null;
            isHostTeam = true;
            isParticipantTeam = null;
            successResponse = {
                results: [
                    {
                        id: 1,
                        team_name: "Host team name 1",
                        created_by: "user 1",
                        team_url: "https://team1.url"
                    },
                    {
                        id: 2,
                        team_name: "Host team name 2",
                        created_by: "user 2",
                        team_url: "https://team2.url"
                    },
                ]
        };
            vm = createController();
            expect(vm.hostTeamCount).toEqual(successResponse.results.length);
        });

        it('403 backend error on getting host team details `hosts/challenge_host_team/`', function () {
            isUserDetails = null;
            isPresentChallenge = null;
            isHostTeam = false;
            isParticipantTeam = null;
            status = 403;
            errorResponse = {
                error: 'error'
            };
            vm = createController();
            expect(vm.error).toEqual(errorResponse);
            expect(vm.isPrivileged).toEqual(false);
        });

        it('401 backend error on getting host team details `hosts/challenge_host_team/`', function () {
            isUserDetails = null;
            isPresentChallenge = null;
            isHostTeam = false;
            isParticipantTeam = null;
            status = 401;
            errorResponse = {
                error: 'error'
            };
            vm = createController();
            expect(window.alert).toHaveBeenCalledWith("Timeout, Please login again to continue!");
            expect(utilities.resetStorage).toHaveBeenCalled();
            expect($state.go).toHaveBeenCalledWith("auth.login");
            expect($rootScope.isAuth).toBeFalsy();
        });

        it('get participated teams details `participants/participant_team`', function () {
            isUserDetails = null;
            isPresentChallenge = null;
            isHostTeam = null;
            isParticipantTeam = true;
            successResponse = {
                results: [
                    {
                        id: 1,
                        team_name: "Participants team name 1",
                        created_by: "user 1",
                        team_url: "https://team1.url"
                    },
                    {
                        id: 2,
                        team_name: "Participants team name 2",
                        created_by: "user 2",
                        team_url: "https://team2.url"
                    },
                ]
            };
            vm = createController();
            expect(vm.participatedTeamCount).toEqual(successResponse.results.length);
        });

        it('403 backend error on getting participated team details `participants/participant_team`', function () {
            isUserDetails = null;
            isPresentChallenge = null;
            isHostTeam = null;
            isParticipantTeam = false;
            status = 403;
            errorResponse = {
                error: 'error'
            };
            vm = createController();
            expect(vm.error).toEqual(errorResponse);
            expect(vm.isPrivileged).toEqual(false);
        });

        it('401 backend error on getting participated team details `participants/participant_team`', function () {
            isUserDetails = null;
            isPresentChallenge = null;
            isHostTeam = null;
            isParticipantTeam = false;
            status = 401;
            errorResponse = {
                error: 'error'
            };
            vm = createController();
            expect(window.alert).toHaveBeenCalledWith("Timeout, Please login again to continue!");
            expect(utilities.resetStorage).toHaveBeenCalled();
            expect($state.go).toHaveBeenCalledWith("auth.login");
            expect($rootScope.isAuth).toBeFalsy();
        });
    });

    describe('Unit tests for hostChallenge function', function () {
        beforeEach(function () {
            spyOn($state, 'go');
        });

        it('redirect to challenge host team page', function () {
            vm.hostChallenge();
            expect($state.go).toHaveBeenCalledWith('web.challenge-host-teams');
        });
    });
});
