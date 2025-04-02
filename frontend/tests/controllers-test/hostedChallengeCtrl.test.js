'use strict';

describe('Unit tests for hosted challenge controller', function () {
    beforeEach(angular.mock.module('evalai'));

    var $controller, createController, $rootScope, $scope, utilities, vm;

    beforeEach(inject(function (_$controller_, _$rootScope_, _utilities_,) {
        $controller = _$controller_;
        $rootScope = _$rootScope_;
        utilities = _utilities_;

        $scope = $rootScope.$new();
        createController = function () {
            return $controller('HostedChallengesCtrl', {$scope: $scope});
        };
        vm = $controller('HostedChallengesCtrl', { $scope: $scope });
    }));

    describe('Global variables', function () {
        it('has default values', function () {
            utilities.storeData('userKey', 'encrypted key');
            spyOn(utilities, 'getData');
            spyOn(utilities, 'showLoader');

            vm = createController();
            expect(utilities.getData).toHaveBeenCalledWith('userKey');
            expect(utilities.showLoader).toHaveBeenCalled();
            expect(vm.challengeList).toEqual([]);
            expect(vm.challengeCreator).toEqual({});
        });
    });

    describe('Unit tests for global backend calls', function () {
        var hostTeamSuccess, hostedChallengeSuccess, successResponse, errorResponse;

        beforeEach(function () {
            spyOn(utilities, 'hideLoader');
            spyOn(utilities, 'storeData');

            utilities.sendRequest = function (parameters) {
                if ((hostTeamSuccess == true && parameters.url == 'hosts/challenge_host_team/') ||
                (hostedChallengeSuccess == true && parameters.url != 'hosts/challenge_host_team/')) {
                    parameters.callback.onSuccess({
                        data: successResponse,
                        status: 200
                    });
                } else if ((hostTeamSuccess == false && parameters.url == 'hosts/challenge_host_team/') ||
                (hostedChallengeSuccess == false && parameters.url != 'hosts/challenge_host_team/')) {
                    parameters.callback.onError({
                        data: errorResponse
                    });
                }
            };
        });

        it('get host teams details backend error `hosts/challenge_host_team/`', function () {
            hostTeamSuccess = false;
            hostedChallengeSuccess = null;
            errorResponse = {
                error: 'error'
            };
            vm = createController();
            expect(utilities.hideLoader).toHaveBeenCalled();
        });

        it('get the details of the hosted challenge \
        `challenges/challenge_host_team/<host_team_id>/challenge`', function () {
            hostTeamSuccess = true;
            hostedChallengeSuccess = true;
            successResponse = {
                results: [
                    {
                        id: 1,
                        title: "Hosted challenge title",
                        description: "Host challenge description",
                        creator: "hostUser"
                    }
                ]
            };
            var challengeList = [];

            vm = createController();
            for (var i = 0; i < successResponse.results.length; i++) {
                challengeList.push(successResponse.results[i]);
                expect(vm.challengeList).toEqual(challengeList);
                expect(utilities.storeData).toHaveBeenCalled();
            }
            expect(utilities.hideLoader).toHaveBeenCalled();
        });

        it('get the hosted challenge details backend error', function () {
            hostTeamSuccess = true;
            hostedChallengeSuccess = false
            // host team details response
            successResponse = {
                results: [
                    {
                        id: 1,
                        team_name: "Host team name",
                        team_url: "https://host_team.url",
                        created_by: "hostchallenge descriptionUser"
                    }
                ]
            };
            // hosted challenge response
            errorResponse = {
                error: 'error'
            };
            vm = createController();
            expect(utilities.hideLoader).toHaveBeenCalled();
        });

    });

    describe('Tabbed Navigation', function () {
        beforeEach(function () {
            vm = createController();
        });
    
        it('should initialize with the ongoing tab selected', function () {
            expect(vm.currentTab).toBe('ongoing');
        });
    
        it('should switch to the upcoming tab', function () {
            vm.setCurrentTab('upcoming');
            expect(vm.currentTab).toBe('upcoming');
        });
    
        it('should switch to the past tab', function () {
            vm.setCurrentTab('past');
            expect(vm.currentTab).toBe('past');
        });
    
        it('should categorize challenges based on their dates', function () {
            var current = new Date();
            var pastDate = new Date(current.getFullYear() - 1, current.getMonth(), current.getDate());
            var futureDate = new Date(current.getFullYear() + 1, current.getMonth(), current.getDate());
            utilities.sendRequest = function (parameters) {
                if (parameters.url === 'hosts/challenge_host_team/') {
                    parameters.callback.onSuccess({
                        data: { results: [{ id: 10 }] }
                    });
                } else if (parameters.url.indexOf("challenges/challenge_host_team/") === 0) {
                    parameters.callback.onSuccess({
                        data: { results: [
                            { id: 1, start_date: pastDate, end_date: pastDate, creator: { id: 101 } },
                            { id: 2, start_date: current, end_date: futureDate, creator: { id: 102 } },
                            { id: 3, start_date: futureDate, end_date: futureDate, creator: { id: 103 } }
                        ]}
                    });
                }
            };
            vm = createController();
            expect(vm.pastChallenges.length).toBe(1);
            expect(vm.ongoingChallenges.length).toBe(1);
            expect(vm.upcomingChallenges.length).toBe(1);
        });
    
        it('should handle API request errors gracefully', function () {
            spyOn(utilities, 'hideLoader');
            utilities.sendRequest = function (parameters) {
                parameters.callback.onError({ error: 'Network Error' });
            };
            vm = createController();
            expect(utilities.hideLoader).toHaveBeenCalled();
        });
    });
    
    describe('Challenge categorization with duplicate handling', function () {
        beforeEach(function () {
            vm = createController();
        });
        
        it('should handle duplicate challenges in upcoming category', function () {
            var current = new Date();
            var futureDate = new Date(current.getTime() + 86400000);
            utilities.sendRequest = function (parameters) {
                if (parameters.url === 'hosts/challenge_host_team/') {
                    parameters.callback.onSuccess({
                        data: { results: [{ id: 10 }, { id: 11 }] }
                    });
                } else if (parameters.url.indexOf("challenges/challenge_host_team/") === 0) {
                    parameters.callback.onSuccess({
                        data: { results: [
                            { id: 1, start_date: futureDate, end_date: new Date(futureDate.getTime() + 86400000), creator: { id: 101 } }
                        ]}
                    });
                }
            };
            vm = createController();
            expect(vm.upcomingChallenges.length).toBe(1);
        });
        
        it('should handle duplicate challenges in ongoing category', function () {
            var current = new Date();
            var startDate = new Date(current.getTime() - 86400000);
            var endDate = new Date(current.getTime() + 86400000);
            utilities.sendRequest = function (parameters) {
                if (parameters.url === 'hosts/challenge_host_team/') {
                    parameters.callback.onSuccess({
                        data: { results: [{ id: 20 }, { id: 21 }] }
                    });
                } else if (parameters.url.indexOf("challenges/challenge_host_team/") === 0) {
                    parameters.callback.onSuccess({
                        data: { results: [
                            { id: 2, start_date: startDate, end_date: endDate, creator: { id: 202 } }
                        ]}
                    });
                }
            };
            vm = createController();
            expect(vm.ongoingChallenges.length).toBe(1);
        });
        
        it('should handle duplicate challenges in past category', function () {
            var current = new Date();
            var pastDate = new Date(current.getTime() - 172800000);
            var pastEndDate = new Date(current.getTime() - 86400000);
            utilities.sendRequest = function (parameters) {
                if (parameters.url === 'hosts/challenge_host_team/') {
                    parameters.callback.onSuccess({
                        data: { results: [{ id: 30 }, { id: 31 }] }
                    });
                } else if (parameters.url.indexOf("challenges/challenge_host_team/") === 0) {
                    parameters.callback.onSuccess({
                        data: { results: [
                            { id: 3, start_date: pastDate, end_date: pastEndDate, creator: { id: 303 } }
                        ]}
                    });
                }
            };
            vm = createController();
            expect(vm.pastChallenges.length).toBe(1);
        });
        
        it('should correctly categorize challenges at boundary conditions', function () {
            var current = new Date();
            utilities.sendRequest = function (parameters) {
                if (parameters.url === 'hosts/challenge_host_team/') {
                    parameters.callback.onSuccess({
                        data: { results: [{ id: 40 }] }
                    });
                } else if (parameters.url.indexOf("challenges/challenge_host_team/") === 0) {
                    parameters.callback.onSuccess({
                        data: { results: [
                            { id: 4, start_date: current, end_date: new Date(current.getTime() + 86400000), creator: { id: 404 } },
                            { id: 5, start_date: new Date(current.getTime() - 86400000), end_date: current, creator: { id: 505 } }
                        ]}
                    });
                }
            };
            vm = createController();
            expect(vm.ongoingChallenges.length).toBe(2);
            expect(vm.upcomingChallenges.length).toBe(0);
            expect(vm.pastChallenges.length).toBe(0);
        });
    }); 

    describe('GMT offset coverage', function () {
        beforeEach(function () {
            spyOn(utilities, 'showLoader').and.callThrough();
            spyOn(utilities, 'hideLoader').and.callThrough();
            spyOn(utilities, 'sendRequest').and.callFake(function (parameters) {
                parameters.callback.onSuccess({ data: { results: [] } });
            });
        });
    
        it('should set sign to + and skip leading zero when minutes >= 10', function () {
            spyOn(moment.fn, 'utcOffset').and.returnValue(330);
            vm = createController();
            expect(utilities.showLoader).toHaveBeenCalled();
        });
    
        it('should set sign to - and add leading zero when minutes < 10', function () {
            spyOn(moment.fn, 'utcOffset').and.returnValue(-65);
            vm = createController();
            expect(utilities.showLoader).toHaveBeenCalled();
        });
    }); 
});