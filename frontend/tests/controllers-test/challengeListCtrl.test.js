'use strict';

describe('Unit tests for challenge list controller', function () {
    beforeEach(angular.mock.module('evalai'));

    var $controller, createController, $rootScope, $scope, utilities, vm, $httpBackend;

    beforeEach(inject(function (_$controller_, _$rootScope_, _utilities_, _$httpBackend_) {
        $controller = _$controller_;
        $rootScope = _$rootScope_;
        utilities = _utilities_;
        $httpBackend = _$httpBackend_;

        $httpBackend.whenGET(/\/api\/challenges\/challenge\/present\/approved\/public\?page=\d+&page_size=\d+/).respond({
            next: null,
            results: []
        });
        $httpBackend.whenGET(/\/api\/challenges\/challenge\/future\/approved\/public\?page=\d+&page_size=\d+/).respond({
            next: null,
            results: []
        });
        $httpBackend.whenGET(/\/api\/challenges\/challenge\/past\/approved\/public\?page=\d+&page_size=\d+/).respond({
            next: null,
            results: []
        });

        spyOn(utilities, 'showLoader');
        spyOn(utilities, 'hideLoader');
        spyOn(utilities, 'hideButton');
        spyOn(utilities, 'storeData');

        $scope = $rootScope.$new();
        createController = function () {
            return $controller('ChallengeListCtrl', {$scope: $scope});
        };
    }));

    afterEach(function() {
        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();
    });

    describe('Global variables', function () {
        it('has default values', function () {
            spyOn(utilities, 'getData').and.returnValue('testUserKey');

            vm = createController();
            $httpBackend.flush();

            expect(utilities.getData).toHaveBeenCalledWith('userKey');
            expect(vm.userKey).toEqual('testUserKey');
            expect(utilities.showLoader).toHaveBeenCalled();
            expect(vm.currentList).toEqual([]);
            expect(vm.upcomingList).toEqual([]);
            expect(vm.pastList).toEqual([]);
            expect(vm.noneCurrentChallenge).toBeTruthy();
            expect(vm.noneUpcomingChallenge).toBeTruthy();
            expect(vm.nonePastChallenge).toBeTruthy();
            expect(vm.challengeCreator).toEqual({});
        });
    });

    describe('Unit tests for global backend calls', function () {
        beforeEach(function() {
            spyOn(utilities, 'getData').and.returnValue('testUserKey');
            
            $httpBackend.resetExpectations();
        });
        
        it('when no ongoing challenge found `challenges/challenge/present/approved/public`', function () {
            $httpBackend.expectGET(/\/api\/challenges\/challenge\/present\/approved\/public\?page=\d+&page_size=\d+/).respond({
                next: null,
                results: []
            });
            $httpBackend.whenGET(/\/api\/challenges\/challenge\/future\/approved\/public\?page=\d+&page_size=\d+/).respond({
                next: null,
                results: []
            });
            $httpBackend.whenGET(/\/api\/challenges\/challenge\/past\/approved\/public\?page=\d+&page_size=\d+/).respond({
                next: null,
                results: []
            });

            vm = createController();
            $httpBackend.flush();
            
            expect(vm.currentList).toEqual([]);
            expect(vm.noneCurrentChallenge).toBeTruthy();
        });

        it('check description length and calculate timezone of ongoing challenge `challenges/challenge/present/approved/public`', function () {
            var mockResults = [
                {
                    id: 1,
                    description: "the length of the ongoing challenge description is greater than or equal to 50",
                    creator: {
                        id: 1
                    },
                    start_date: "Fri June 12 2018 22:41:51 GMT+0530",
                    end_date: "Fri June 12 2099 22:41:51 GMT+0530"
                },
                {
                    id: 2,
                    description: "random description",
                    creator: {
                        id: 1
                    },
                    start_date: "Sat May 26 2015 22:41:51 GMT+0530",
                    end_date: "Sat May 26 2099 22:41:51 GMT+0530"
                }
            ];
            
            $httpBackend.expectGET(/\/api\/challenges\/challenge\/present\/approved\/public\?page=\d+&page_size=\d+/).respond({
                next: null,
                results: mockResults
            });
            $httpBackend.whenGET(/\/api\/challenges\/challenge\/future\/approved\/public\?page=\d+&page_size=\d+/).respond({
                next: null,
                results: []
            });
            $httpBackend.whenGET(/\/api\/challenges\/challenge\/past\/approved\/public\?page=\d+&page_size=\d+/).respond({
                next: null,
                results: []
            });

            vm = createController();
            $httpBackend.flush();
            
            expect(vm.currentList.length).toEqual(2);
            expect(vm.noneCurrentChallenge).toBeFalsy();

            var timezone = moment.tz.guess();
            var zone = moment.tz.zone(timezone);
            for (var i in vm.currentList) {
                if (vm.currentList[i].description.length >= 50) {
                    expect(vm.currentList[i].isLarge).toEqual("...");
                } else {
                    expect(vm.currentList[i].isLarge).toEqual("");
                }
                var offset = new Date(vm.currentList[i].start_date).getTimezoneOffset();
                expect(vm.currentList[i].time_zone).toEqual(zone.abbr(offset));
                expect(vm.challengeCreator[vm.currentList[i].id]).toEqual(vm.currentList[i].creator.id);
            }
            
            expect(utilities.storeData).toHaveBeenCalledWith("challengeCreator", vm.challengeCreator);
        });

        it('ongoing challenge backend error `challenges/challenge/present/approved/public`', function () {
            $httpBackend.expectGET(/\/api\/challenges\/challenge\/present\/approved\/public\?page=\d+&page_size=\d+/).respond(500, {
                error: 'error'
            });
            $httpBackend.whenGET(/\/api\/challenges\/challenge\/future\/approved\/public\?page=\d+&page_size=\d+/).respond({
                next: null,
                results: []
            });
            $httpBackend.whenGET(/\/api\/challenges\/challenge\/past\/approved\/public\?page=\d+&page_size=\d+/).respond({
                next: null,
                results: []
            });

            vm = createController();
            $httpBackend.flush();
            
            expect(utilities.hideLoader).toHaveBeenCalled();
            expect(vm.noneCurrentChallenge).toBeTruthy();
        });

        it('when no upcoming challenge found `challenges/challenge/future/approved/public`', function () {
            $httpBackend.whenGET(/\/api\/challenges\/challenge\/present\/approved\/public\?page=\d+&page_size=\d+/).respond({
                next: null,
                results: []
            });
            $httpBackend.expectGET(/\/api\/challenges\/challenge\/future\/approved\/public\?page=\d+&page_size=\d+/).respond({
                next: null,
                results: []
            });
            $httpBackend.whenGET(/\/api\/challenges\/challenge\/past\/approved\/public\?page=\d+&page_size=\d+/).respond({
                next: null,
                results: []
            });

            vm = createController();
            $httpBackend.flush();
            
            expect(vm.upcomingList).toEqual([]);
            expect(vm.noneUpcomingChallenge).toBeTruthy();
        });

        it('check description length and calculate timezone of upcoming challenge `challenges/challenge/future`', function () {
            var mockResults = [
                {
                    id: 1,
                    description: "the length of the upcoming challenge description is greater than or equal to 50",
                    creator: {
                        id: 1
                    },
                    start_date: "Fri June 12 2018 22:41:51 GMT+0530",
                    end_date: "Fri June 12 2099 22:41:51 GMT+0530"
                },
                {
                    id: 2,
                    description: "random description",
                    creator: {
                        id: 1
                    },
                    start_date: "Sat May 26 2015 22:41:51 GMT+0530",
                    end_date: "Sat May 26 2099 22:41:51 GMT+0530"
                }
            ];
            
            $httpBackend.whenGET(/\/api\/challenges\/challenge\/present\/approved\/public\?page=\d+&page_size=\d+/).respond({
                next: null,
                results: []
            });
            $httpBackend.expectGET(/\/api\/challenges\/challenge\/future\/approved\/public\?page=\d+&page_size=\d+/).respond({
                next: null,
                results: mockResults
            });
            $httpBackend.whenGET(/\/api\/challenges\/challenge\/past\/approved\/public\?page=\d+&page_size=\d+/).respond({
                next: null,
                results: []
            });

            vm = createController();
            $httpBackend.flush();
            
            expect(vm.upcomingList.length).toEqual(2);
            expect(vm.noneUpcomingChallenge).toBeFalsy();

            var timezone = moment.tz.guess();
            var zone = moment.tz.zone(timezone);
            for (var i in vm.upcomingList) {
                if (vm.upcomingList[i].description.length >= 50) {
                    expect(vm.upcomingList[i].isLarge).toEqual("...");
                } else {
                    expect(vm.upcomingList[i].isLarge).toEqual("");
                }
                var offset = new Date(vm.upcomingList[i].start_date).getTimezoneOffset();
                expect(vm.upcomingList[i].time_zone).toEqual(zone.abbr(offset));
                expect(vm.challengeCreator[vm.upcomingList[i].id]).toEqual(vm.upcomingList[i].creator.id);
            }
            
            expect(utilities.storeData).toHaveBeenCalledWith("challengeCreator", vm.challengeCreator);
        });

        it('upcoming challenge backend error `challenges/challenge/future/approved/public`', function () {
            $httpBackend.whenGET(/\/api\/challenges\/challenge\/present\/approved\/public\?page=\d+&page_size=\d+/).respond({
                next: null,
                results: []
            });
            $httpBackend.expectGET(/\/api\/challenges\/challenge\/future\/approved\/public\?page=\d+&page_size=\d+/).respond(500, {
                error: 'error'
            });
            $httpBackend.whenGET(/\/api\/challenges\/challenge\/past\/approved\/public\?page=\d+&page_size=\d+/).respond({
                next: null,
                results: []
            });

            vm = createController();
            $httpBackend.flush();
            
            expect(utilities.hideLoader).toHaveBeenCalled();
            expect(vm.noneUpcomingChallenge).toBeTruthy();
        });

        it('when no past challenge found `challenges/challenge/past/approved/public`', function () {
            $httpBackend.whenGET(/\/api\/challenges\/challenge\/present\/approved\/public\?page=\d+&page_size=\d+/).respond({
                next: null,
                results: []
            });
            $httpBackend.whenGET(/\/api\/challenges\/challenge\/future\/approved\/public\?page=\d+&page_size=\d+/).respond({
                next: null,
                results: []
            });
            $httpBackend.expectGET(/\/api\/challenges\/challenge\/past\/approved\/public\?page=\d+&page_size=\d+/).respond({
                next: null,
                results: []
            });

            vm = createController();
            $httpBackend.flush();
            
            expect(vm.pastList).toEqual([]);
            expect(vm.nonePastChallenge).toBeTruthy();
        });

        it('check description length and calculate timezone of past challenge `challenges/challenge/past/approved/public`', function () {
            var mockResults = [
                {
                    id: 1,
                    description: "the length of the past challenge description is greater than or equal to 50",
                    creator: {
                        id: 1
                    },
                    start_date: "Fri June 12 2018 22:41:51 GMT+0530",
                    end_date: "Fri June 12 2099 22:41:51 GMT+0530"
                },
                {
                    id: 2,
                    description: "random description",
                    creator: {
                        id: 1
                    },
                    start_date: "Sat May 26 2015 22:41:51 GMT+0530",
                    end_date: "Sat May 26 2099 22:41:51 GMT+0530"
                }
            ];
            
            $httpBackend.whenGET(/\/api\/challenges\/challenge\/present\/approved\/public\?page=\d+&page_size=\d+/).respond({
                next: null,
                results: []
            });
            $httpBackend.whenGET(/\/api\/challenges\/challenge\/future\/approved\/public\?page=\d+&page_size=\d+/).respond({
                next: null,
                results: []
            });
            $httpBackend.expectGET(/\/api\/challenges\/challenge\/past\/approved\/public\?page=\d+&page_size=\d+/).respond({
                next: null,
                results: mockResults
            });

            vm = createController();
            $httpBackend.flush();
            
            expect(vm.pastList.length).toEqual(2);
            expect(vm.nonePastChallenge).toBeFalsy();

            var timezone = moment.tz.guess();
            var zone = moment.tz.zone(timezone);
            for (var i in vm.pastList) {
                if (vm.pastList[i].description.length >= 50) {
                    expect(vm.pastList[i].isLarge).toEqual("...");
                } else {
                    expect(vm.pastList[i].isLarge).toEqual("");
                }
                var offset = new Date(vm.pastList[i].start_date).getTimezoneOffset();
                expect(vm.pastList[i].time_zone).toEqual(zone.abbr(offset));
                expect(vm.challengeCreator[vm.pastList[i].id]).toEqual(vm.pastList[i].creator.id);
            }
            
            expect(utilities.storeData).toHaveBeenCalledWith("challengeCreator", vm.challengeCreator);
            expect(utilities.hideLoader).toHaveBeenCalled();
        });

        it('past challenge backend error `challenges/challenge/past/approved/public`', function () {
            $httpBackend.whenGET(/\/api\/challenges\/challenge\/present\/approved\/public\?page=\d+&page_size=\d+/).respond({
                next: null,
                results: []
            });
            $httpBackend.whenGET(/\/api\/challenges\/challenge\/future\/approved\/public\?page=\d+&page_size=\d+/).respond({
                next: null,
                results: []
            });
            $httpBackend.expectGET(/\/api\/challenges\/challenge\/past\/approved\/public\?page=\d+&page_size=\d+/).respond(500, {
                error: 'error'
            });

            vm = createController();
            $httpBackend.flush();
            
            expect(utilities.hideLoader).toHaveBeenCalled();
            expect(vm.nonePastChallenge).toBeTruthy();
        });

        it('should call getAllResults method recursively when next is not null', function () {
            $httpBackend.resetExpectations();
            
            vm = createController();
            
            spyOn(vm, 'getAllResults').and.callThrough();
            
            var parameters = {
                url: 'challenges/challenge/present/approved/public',
                method: 'GET',
                recursiveTest: true
            };
            
            $httpBackend.expectGET(/\/api\/challenges\/challenge\/present\/approved\/public\?page=\d+&page_size=\d+/).respond({
                next: 'http://127.0.0.1:8888/api/challenges/challenge/present/approved/public?page=2&page_size=12',
                results: [
                    {
                        id: 1,
                        description: "the length of the ongoing challenge description is greater than or equal to 50",
                        creator: { id: 1 },
                        start_date: "Fri June 12 2018 22:41:51 GMT+0530",
                        end_date: "Fri June 12 2099 22:41:51 GMT+0530"
                    }
                ]
            });
            
            $httpBackend.expectGET('http://127.0.0.1:8888/api/challenges/challenge/present/approved/public?page=2&page_size=12').respond({
                next: null,
                results: [
                    {
                        id: 2,
                        description: "second page",
                        creator: { id: 1 },
                        start_date: "Fri June 12 2018 22:41:51 GMT+0530",
                        end_date: "Fri June 12 2099 22:41:51 GMT+0530"
                    }
                ]
            });
            
            vm.getAllResults(parameters, vm.currentList, "noneCurrentChallenge", "current");
            $httpBackend.flush();
            
            expect(vm.getAllResults.calls.count()).toBeGreaterThan(1);
            expect(vm.currentList.length).toEqual(2);
            expect(vm.noneCurrentChallenge).toBeFalsy();
        });
    });
});