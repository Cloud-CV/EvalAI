'use strict';

describe('Unit tests for challenge controller', function () {
    beforeEach(angular.mock.module('evalai'));

    var $controller, createController, $injector, $rootScope, $state, $scope, utilities, $http, $interval, $mdDialog, moment, vm;

    beforeEach(inject(function (_$controller_, _$injector_,  _$rootScope_, _$state_, _utilities_, _$http_, _$interval_, _$mdDialog_, _moment_) {
        $controller = _$controller_;
        $injector = _$injector_;
        $rootScope = _$rootScope_;
        $state = _$state_;
        utilities = _utilities_;
        $http = _$http_;
        $interval = _$interval_;
        $mdDialog = _$mdDialog_;
        moment = _moment_;
        
        $scope = $rootScope.$new();
        createController = function () {
            return $controller('ChallengeCtrl', {$scope: $scope});
        };
        vm = $controller('ChallengeCtrl', { $scope: $scope });
    }));

    describe('Global variables', function () {
        it('has default values', function () {
            expect(vm.phaseId).toEqual(null);
            expect(vm.input_file).toEqual(null);
            expect(vm.methodName).toEqual("");
            expect(vm.methodDesc).toEqual("");
            expect(vm.projectUrl).toEqual("");
            expect(vm.publicationUrl).toEqual("");
            expect(vm.page).toEqual({});
            expect(vm.isParticipated).toEqual(false);
            expect(vm.isActive).toEqual(false);
            expect(vm.phaseRemainingSubmissions).toEqual({});
            expect(vm.phaseRemainingSubmissionsFlags).toEqual({});
            expect(vm.phaseRemainingSubmissionsCountdown).toEqual({});
            expect(vm.subErrors).toEqual({});
            expect(vm.isExistLoader).toEqual(false);
            expect(vm.loaderTitle).toEqual('');
            expect(vm.termsAndConditions).toEqual(false);
            expect(vm.lastKey).toEqual(null);
            expect(vm.sortColumn).toEqual('rank');
            expect(vm.columnIndexSort).toEqual(0);
            expect(vm.reverseSort).toEqual(false);
            expect(vm.poller).toEqual(null);
            expect(vm.isResult).toEqual(false);
            expect(vm.initial_ranking).toEqual({});
            expect(vm.submissionVisibility).toEqual({});
            expect(vm.baselineStatus).toEqual({});
            expect(vm.team).toEqual({});
            expect(vm.isPublished).toEqual(false);

            utilities.storeData('userKey', 'encrypted key');
        });
    });

    describe('Unit tests for all the global backend calls', function () {
        var challengeSuccess, successResponse, errorResponse, status, challengePhaseSuccess;
        var challengePhaseSplitSuccess, participantTeamChallengeSuccess, participantTeamSuccess, selectExistTeamSuccess;
        var challengeSuccessResponse, participantTeamSuccessResponse, participantTeamChallengeSuccessResponse
        var challengePhaseSplit = false;
        var team_list = [
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

            utilities.sendRequest = function (parameters) {
                // set successResponse according to the requested url
                if (participantTeamSuccess == true && parameters.url == 'participants/participant_team') {
                    successResponse = participantTeamSuccessResponse;
                } else if (challengeSuccess == true && parameters.url == 'challenges/challenge/undefined/') {
                    successResponse = challengeSuccessResponse;
                } else if (participantTeamChallengeSuccess == true && parameters.url == 'participants/participant_teams/challenges/undefined/user') {
                    successResponse = participantTeamChallengeSuccessResponse;
                }

                if ((challengePhaseSuccess == true && parameters.url == 'challenges/challenge/undefined/challenge_phase') ||
                (challengeSuccess == true && parameters.url == 'challenges/challenge/undefined/') ||
                (challengePhaseSplitSuccess == true && parameters.url == 'challenges/undefined/challenge_phase_split') ||
                (participantTeamChallengeSuccess == true && parameters.url == 'participants/participant_teams/challenges/undefined/user') ||
                (participantTeamSuccess == true && parameters.url == 'participants/participant_team') ||
                (selectExistTeamSuccess == true && parameters.url == 'challenges/challenge/undefined/participant_team/null')) {

                    parameters.callback.onSuccess({
                        status: 200,
                        data: successResponse
                    });
                } else if ((challengePhaseSuccess == false && parameters.url == 'challenges/challenge/undefined/challenge_phase') ||
                (challengeSuccess == false && parameters.url == 'challenges/challenge/undefined/') ||
                (challengePhaseSplitSuccess == false && parameters.url == 'challenges/undefined/challenge_phase_split') ||
                (participantTeamChallengeSuccess == false && parameters.url == 'participants/participant_teams/challenges/undefined/user') ||
                (participantTeamSuccess == false && parameters.url == 'participants/participant_team') ||
                (selectExistTeamSuccess == false && parameters.url == 'challenges/challenge/undefined/participant_team/null')){

                    parameters.callback.onError({
                        data: errorResponse,
                        status: status
                    });
                }
            };
        });

        it('get the details of the particular challenge \
            `challenges/challenge/<challenge_id>/`', function () {
            challengeSuccess = true;
            challengePhaseSuccess = null;
            challengePhaseSplitSuccess = null;
            participantTeamChallengeSuccess = null;
            participantTeamSuccess = null;
            selectExistTeamSuccess = null;

            challengeSuccessResponse = {
                is_active: true,
                published: false,
                enable_forum: true,
                forum_url: "http://example.com",
                cli_version: "evalai-cli version",
                image: 'logo.png',
            };
            vm = createController();
            expect(vm.page).toEqual(challengeSuccessResponse);
            expect(vm.isActive).toEqual(challengeSuccessResponse.is_active);
            expect(vm.isPublished).toEqual(challengeSuccessResponse.published);
            expect(vm.isForumEnabled).toEqual(challengeSuccessResponse.enable_forum);
            expect(vm.forumURL).toEqual(challengeSuccessResponse.forum_url);
            expect(vm.cliVersion).toEqual(challengeSuccessResponse.cli_version);
        });

        it('when challenge logo image is null', function () {
            challengeSuccess = true;
            challengePhaseSuccess = null;
            challengePhaseSplitSuccess = null;
            participantTeamChallengeSuccess = null;
            participantTeamSuccess = null;
            selectExistTeamSuccess = null;

            challengeSuccessResponse = {
                is_active: true,
                published: false,
                enable_forum: true,
                forum_url: "http://example.com",
                cli_version: "evalai-cli version",
                image: null,
            };
            vm = createController();
            expect(vm.page.image).toEqual("dist/images/logo.png");
        });

        it('get details of challenges corresponding to participant teams of that user \
            `participants/participant_teams/challenges/<challenge_id>/user`', function () {
            challengeSuccess = true;
            participantTeamChallengeSuccess = true;
            challengePhaseSuccess = null;
            challengePhaseSplitSuccess = null;
            participantTeamSuccess = null;
            selectExistTeamSuccess = null;
            utilities.storeData('userKey', 'encrypted key');

            // get challenge details response
            challengeSuccessResponse = {
                is_active: true,
                published: false,
                enable_forum: true,
                forum_url: "http://example.com",
                cli_version: "evalai-cli version",
                image: 'logo.png',
            };

            // get details of challenges corresponding to participant teams response
            participantTeamChallengeSuccessResponse = {
                challenge_participant_team_list: {
                    first_object: {
                        challenge: {
                            id: undefined,
                            title: "Challenge title",
                            description: "Challenge description"
                        },
                    }
                },
                datetime_now: "timezone.now",
                is_challenge_host: true,
            };

            vm = createController();
            expect(vm.currentDate).toEqual(participantTeamChallengeSuccessResponse.datetime_now);
            expect(vm.isParticipated).toBeTruthy();
            expect(vm.isChallengeHost).toBeTruthy();
        });

        team_list.forEach(response => {
            it('pagination next is ' + response.next + ' and previous is ' + response.previous + '\
                `participants/participant_team`', function () {;
                challengeSuccess = true;    
                participantTeamChallengeSuccess = true;
                participantTeamSuccess = true;
                selectExistTeamSuccess = null;
                challengePhaseSuccess = null;
                challengePhaseSplitSuccess = null;

                // get challenge details response
                challengeSuccessResponse = {
                    is_active: true,
                    published: false,
                    enable_forum: true,
                    forum_url: "http://example.com",
                    cli_version: "evalai-cli version",
                    image: 'logo.png',
                };

                // get details of challenges corresponding to participant teams response
                participantTeamChallengeSuccessResponse = {
                    challenge_participant_team_list: {
                        first_object: {
                            challenge: {
                                id: 3,
                                title: "Challenge title",
                                description: "Challenge description"
                            },
                        }
                    },
                    datetime_now: "timezone.now",
                    is_challenge_host: true,
                };

                // participant team details response
                participantTeamSuccessResponse = response;
                participantTeamSuccessResponse.results = [
                    {
                        is_public: false,
                        start_date: "Fri June 12 2018 22:41:51 GMT+0530",
                        end_date: "Fri June 12 2099 22:41:51 GMT+0530"
                    },
                ];
                utilities.storeData('userKey', 'encrypted key');

                vm = createController();
                expect(vm.existTeam).toEqual(participantTeamSuccessResponse);
                expect(vm.showPagination).toBeTruthy();
                expect(vm.paginationMsg).toEqual('');
                expect(utilities.deleteData).toHaveBeenCalledWith('emailError');

                if (participantTeamSuccessResponse.next == null) {
                    expect(vm.isNext).toEqual('disabled');
                    expect(vm.currentPage).toEqual(1);
                } else {
                    expect(vm.isNext).toEqual('');
                    expect(vm.currentPage).toEqual(participantTeamSuccessResponse.next.split('page=')[1] - 1);
                }

                if (participantTeamSuccessResponse.previous == null) {
                    expect(vm.isPrev).toEqual('disabled');
                } else {
                    expect(vm.isPrev).toEqual('');
                }

                if (participantTeamSuccessResponse.next !== null) {
                    expect(vm.currentPage).toEqual(participantTeamSuccessResponse.next.split('page=')[1] - 1);
                } else {
                    expect(vm.currentPage).toEqual(1);
                }
            });
        });

        it('success of selectExistTeam function \
        `challenges/challenge/<challenge_id>/participant_team/<team_id>`', function () {
            challengeSuccess = true;
            participantTeamChallengeSuccess = true;
            participantTeamSuccess = true;
            selectExistTeamSuccess = true;
            challengePhaseSuccess = null;
            challengePhaseSplitSuccess = null;

            // get challenge details response
            challengeSuccessResponse = {
                is_active: true,
                published: false,
                enable_forum: true,
                forum_url: "http://example.com",
                cli_version: "evalai-cli version",
                image: 'logo.png',
            };

            // get details of challenges corresponding to participant teams response
            participantTeamChallengeSuccessResponse = {
                challenge_participant_team_list: {
                    first_object: {
                        challenge: null
                    }
                },
                datetime_now: "timezone.now",
                is_challenge_host: true,
            };

            // get participant team details response
            participantTeamSuccessResponse = {
                next: 'page=4',
                previous: 'page=2',
                results: {
                    is_public: false,
                    start_date: "Fri June 12 2018 22:41:51 GMT+0530",
                    end_date: "Fri June 12 2099 22:41:51 GMT+0530"
                }
            };
            utilities.storeData('userKey', 'encrypted key');

            vm = createController();
            spyOn(vm, 'startLoader');
            spyOn(vm, 'stopLoader');
            spyOn($state, 'go');
            spyOn(angular, 'element');
            vm.selectExistTeam();
            expect(vm.loaderTitle).toEqual('');
            expect(angular.element).toHaveBeenCalledWith('.exist-team-card');
            expect(vm.startLoader).toHaveBeenCalledWith("Loading Teams");
            expect(vm.isParticipated).toBeTruthy();
            expect($state.go).toHaveBeenCalledWith('web.challenge-main.challenge-page.submission');
            expect(vm.stopLoader).toHaveBeenCalled();
        });

        it('404 backend error of selectExistTeam function \
        `challenges/challenge/<challenge_id>/participant_team/<team_id>`', function () {
            challengeSuccess = true;
            participantTeamChallengeSuccess = true;
            participantTeamSuccess = true;
            selectExistTeamSuccess = null;
            challengePhaseSuccess = null;
            challengePhaseSplitSuccess = null;

            // get challenge details response
            challengeSuccessResponse = {
                is_active: true,
                published: false,
                enable_forum: true,
                forum_url: "http://example.com",
                cli_version: "evalai-cli version",
                image: 'logo.png',
            };

            // get details of challenges corresponding to participant teams response
            participantTeamChallengeSuccessResponse = {
                challenge_participant_team_list: {
                    first_object: {
                        challenge: null
                    }
                },
                datetime_now: "timezone.now",
                is_challenge_host: true,
            };

            // get participant team details response
            participantTeamSuccessResponse = {
                next: 'page=4',
                previous: 'page=2',
                results: {
                    is_public: false,
                    start_date: "Fri June 12 2018 22:41:51 GMT+0530",
                    end_date: "Fri June 12 2099 22:41:51 GMT+0530"
                }
            };
            utilities.storeData('userKey', 'encrypted key');

            status = !404
            errorResponse = {
                error: 'error'
            };
            vm = createController();
            spyOn(vm, 'startLoader');
            spyOn(vm, 'stopLoader');
            spyOn($rootScope, 'notify');
            spyOn(angular, 'element');

            selectExistTeamSuccess = false;
            vm.selectExistTeam();
            expect(vm.loaderTitle).toEqual('');
            expect(angular.element).toHaveBeenCalledWith('.exist-team-card');
            expect(vm.startLoader).toHaveBeenCalledWith("Loading Teams");
            expect($rootScope.notify).toHaveBeenCalledWith("error", errorResponse.error);
            expect(vm.stopLoader).toHaveBeenCalled();
        });

        it('to load data with pagination', function () {
            challengeSuccess = true;
            participantTeamChallengeSuccess = true;
            participantTeamSuccess = true;
            selectExistTeamSuccess = null;
            challengePhaseSuccess = null;
            challengePhaseSplitSuccess = null;

            // get challenge details response
            challengeSuccessResponse = {
                is_active: true,
                published: false,
                enable_forum: true,
                forum_url: "http://example.com",
                cli_version: "evalai-cli version",
                image: 'logo.png',
            };

            // get details of challenges corresponding to participant teams response
            participantTeamChallengeSuccessResponse = {
                challenge_participant_team_list: {
                    first_object: {
                        challenge: {
                            id: 1,
                            title: "Challenge title",
                            description: "Challenge description"
                        },
                    }
                },
                datetime_now: "timezone.now",
                is_challenge_host: true,
            };

            // get participant team details response
            participantTeamSuccessResponse = {
                next: 'page=4',
                previous: 'page=2',
                results: {
                    is_public: false,
                    start_date: "Fri June 12 2018 22:41:51 GMT+0530",
                    end_date: "Fri June 12 2099 22:41:51 GMT+0530"
                }
            };
            utilities.storeData('userKey', 'encrypted key');
       
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

        it('backend error of the particular challenge `challenges/challenge/<challenge_id>/', function () {
            challengeSuccess = false;
            participantTeamChallengeSuccess = null;
            participantTeamSuccess = null;
            selectExistTeamSuccess = null;
            challengePhaseSuccess = null;
            challengePhaseSplitSuccess = null;

            status = 404;
            errorResponse = {
                error: 'email error'
            };
            spyOn($state, 'go');
            spyOn($rootScope, 'notify');
            spyOn(utilities, 'hideLoader');
            vm = createController();
            expect($rootScope.notify).toHaveBeenCalledWith('error', errorResponse.error);
            expect($state.go).toHaveBeenCalledWith('web.dashboard');
            expect(utilities.hideLoader).toHaveBeenCalled();
        });

        it('get details of the particular challenge phase `challenges/challenge/<challenge_id>/challenge_phase`', function () {
            challengeSuccess = null;
            participantTeamChallengeSuccess = null;
            participantTeamSuccess = null;
            selectExistTeamSuccess = null;
            challengePhaseSuccess = true;
            challengePhaseSplitSuccess = null;

            // get challenge phase details response
            successResponse = {
                results: [
                    {
                        is_public: false,
                        start_date: "Fri June 12 2018 22:41:51 GMT+0530",
                        end_date: "Fri June 12 2099 22:41:51 GMT+0530"
                    },
                ],
            };
            spyOn(utilities, 'hideLoader');
            vm = createController();
            expect(vm.phases).toEqual(successResponse);
            var timezone = moment.tz.guess();
            for (var i = 0; i < successResponse.count; i++) {
                expect(successResponse.results[i].is_public).toBeFalsy();
                expect(vm.phases.results[i].showPrivate).toBeTruthy();
            }

            for(var i = 0; i < successResponse.results.length; i++){
                var offset = new Date(successResponse.results[i].start_date).getTimezoneOffset();
                expect(vm.phases.results[i].start_zone).toEqual(moment.tz.zone(timezone).abbr(offset));
                offset = new Date(successResponse.results[i].end_date).getTimezoneOffset();
                expect(vm.phases.results[i].end_zone).toEqual(moment.tz.zone(timezone).abbr(offset));
            }
            expect(utilities.hideLoader).toHaveBeenCalled();
        });

        it('backend error of particular challenge phase `challenges/challenge/<challenge_id>/challenge_phase`', function () {
            challengeSuccess = null;
            participantTeamChallengeSuccess = null;
            participantTeamSuccess = null;
            selectExistTeamSuccess = null;
            challengePhaseSuccess = false;
            challengePhaseSplitSuccess = null;

            status = 404;
            errorResponse = {
                detail: 'error'
            };
            spyOn(utilities, 'storeData');
            spyOn($state, 'go');
            spyOn(utilities, 'hideLoader');
            vm = createController();
            expect(utilities.storeData).toHaveBeenCalledWith('emailError', errorResponse.detail);
            expect($state.go).toHaveBeenCalledWith('web.permission-denied');
            expect(utilities.hideLoader).toHaveBeenCalled();
        });

        it('get details of the particular challenge phase split `challenges/<challenge_id>/challenge_phase_split`', function () {
            challengeSuccess = null;
            participantTeamChallengeSuccess = null;
            participantTeamSuccess = null;
            selectExistTeamSuccess = null;
            challengePhaseSuccess = null;
            challengePhaseSplitSuccess = true;

            challengePhaseSplit = true;
            // get challenge phase split details response
            successResponse = [
                {
                    visibility: 2,
                    host: 1
                }
            ];
            var challengePhaseVisibility = {
                owner_and_host: 1,
                host: 2,
                public: 3,
            };
            spyOn(utilities, 'hideLoader');
            vm.isParticipated = true;
            vm = createController();
            expect(vm.phaseSplits).toEqual(successResponse);
            for(var i = 0; i < successResponse.length; i++) {
                if (successResponse[i].visibility != challengePhaseVisibility.public) {
                    expect(vm.phaseSplits[i].showPrivate).toBeTruthy();
                }
            }
            expect(utilities.hideLoader).toHaveBeenCalled();
        });

        it('backend error of particular challenge phase split `challenges/<challenge_id>/challenge_phase_split`', function () {
            challengeSuccess = null;
            participantTeamChallengeSuccess = null;
            participantTeamSuccess = null;
            selectExistTeamSuccess = null;
            challengePhaseSuccess = null;
            challengePhaseSplitSuccess = false;

            status = 404;
            errorResponse = {
                detail: 'error'
            };
            spyOn(utilities, 'storeData');
            spyOn($state, 'go');
            spyOn(utilities, 'hideLoader');
            vm = createController();
            expect(utilities.storeData).toHaveBeenCalledWith('emailError', errorResponse.detail);
            expect($state.go).toHaveBeenCalledWith('web.permission-denied');
            expect(utilities.hideLoader).toHaveBeenCalled();
        });
    });

    describe('Unit tests for displayDockerSubmissionInstructions function \
        `jobs/<challenge_id>/remaining_submissions`', function () {
        var success, successResponse;
        var errorResponse = {
            detail: 'Email Error'
        };

        beforeEach(function () {
            spyOn(utilities, 'hideLoader');
            spyOn(utilities, 'storeData');
            spyOn($state, 'go');

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

        it('when submission limit exceeded', function () {
            successResponse = {
                phases: [
                    {
                        id: 1,
                        limits: {
                            submission_limit_exceeded: true,
                            remaining_submissions_today_count: 12,
                            remaining_time: 12/12/12,
                        }
                    },
                ]
            };
            success = true;
            vm.displayDockerSubmissionInstructions(true, true);
            expect(vm.phaseRemainingSubmissions).toEqual(successResponse);
            var details = vm.phaseRemainingSubmissions.phases;
            for (var i=0; i < details.length; i++) {
                expect(vm.phaseRemainingSubmissionsFlags[details[i].id]).toEqual('maxExceeded');
            }
            expect(utilities.hideLoader).toHaveBeenCalled();
        });

        it('when todays remaining submission count greater than 0', function () {
            successResponse = {
                phases: [
                    {
                        id: 1,
                        limits: {
                            submission_limit_exceeded: false,
                            remaining_submissions_today_count: 12,
                            remaining_time: 12/12/12,
                        }
                    },
                ]
            };
            success = true;
            vm.displayDockerSubmissionInstructions(true, true);
            expect(vm.phaseRemainingSubmissions).toEqual(successResponse);
            var details = vm.phaseRemainingSubmissions.phases;
            for (var i=0; i < details.length; i++) {
                expect(vm.phaseRemainingSubmissionsFlags[details[i].id]).toEqual('showSubmissionNumbers');
            }
            expect(utilities.hideLoader).toHaveBeenCalled();
        });

        it('when submission limit exceeded & todays remaining submission count less than 0', function () {
            successResponse = {
                phases: [
                    {
                        id: 1,
                        limits: {
                            submission_limit_exceeded: false,
                            remaining_submissions_today_count: 0,
                            remaining_time: 12/12/12,
                        }
                    },
                ]
            };
            success = true;
            vm.displayDockerSubmissionInstructions(true, true);
            expect(vm.phaseRemainingSubmissions).toEqual(successResponse);
            var details = vm.phaseRemainingSubmissions.phases;
            for (var i=0; i < details.length; i++) {
                expect(vm.eachPhase).toEqual(details[i]);
                expect(vm.phaseRemainingSubmissionsFlags[details[i].id]).toEqual('showClock');

                // Unit tests for `countDownTimer` function
                expect(vm.remainingTime).toEqual(vm.eachPhase.limits.remaining_time);
                expect(vm.days).toEqual(Math.floor(vm.remainingTime / 24 / 60 / 60));
                expect(vm.hoursLeft).toEqual(Math.floor((vm.remainingTime) - (vm.days * 86400)));
                expect(vm.hours).toEqual(Math.floor(vm.hoursLeft / 3600));
                expect(vm.minutesLeft).toEqual(Math.floor((vm.hoursLeft) - (vm.hours * 3600)));
                expect(vm.minutes).toEqual(Math.floor(vm.minutesLeft / 60));
                if (vm.remainingTime === 0) {
                    expect(vm.phaseRemainingSubmissionsFlags[vm.eachPhase.id]).toEqual('showSubmissionNumbers');
                }
            }
            expect(utilities.hideLoader).toHaveBeenCalled();
        });

        it('backend error', function () {
            success = false;
            vm.displayDockerSubmissionInstructions(true, true);
            expect(utilities.storeData).toHaveBeenCalledWith('emailError', errorResponse.detail);
            expect($state.go).toHaveBeenCalledWith('web.permission-denied');
        });
    });

    describe('Unit tests for makeSubmission function \
        `jobs/challenge/<challenge_id>/challenge_phase/<phase_id>/submission/`', function () {
        var success, status;
        var errorResponse = {
            error: 'error',
        };
        var successResponse = {
            success: 'success',
        };

        beforeEach(function() {
            spyOn(vm, 'startLoader');
            spyOn(vm, 'stopLoader');
            spyOn($rootScope, 'notify');

            utilities.sendRequest = function (parameters) {
                if (success) {
                    parameters.callback.onSuccess({
                        status: 200,
                        data: successResponse
                    });
                } else {
                    parameters.callback.onError({
                        status: status,
                        data: errorResponse
                    });
                }
            };
        });

        it('succesfully submission', function () {
            success = true;
            vm.isParticipated = true;
            vm.makeSubmission();
            expect(vm.startLoader).toHaveBeenCalledWith('Making Submission');
            expect($rootScope.notify).toHaveBeenCalledWith('success', 'Your submission has been recorded succesfully!');
            expect(vm.stopLoader).toHaveBeenCalled();
        });

        it('404 backend error', function () {
            success = false;
            status = 404;
            vm.isParticipated = true;
            vm.isSubmissionUsingUrl = false;
            vm.makeSubmission();
            vm.fileVal = 'submission.zip';
            expect(vm.phaseId).toEqual(null);
            expect(vm.methodName).toEqual(null);
            expect(vm.methodDesc).toEqual(null);
            expect(vm.projectUrl).toEqual(null);
            expect(vm.publicationUrl).toEqual(null);
            expect(vm.subErrors.msg).toEqual('Please select phase!');
            expect(vm.stopLoader).toHaveBeenCalled();
        });

        it('other backend error', function () {
            success = false;
            status = 403;
            vm.isParticipated = true;
            vm.isSubmissionUsingUrl = false;
            vm.makeSubmission('submission.zip');
            expect(vm.phaseId).toEqual(null);
            expect(vm.methodName).toEqual(null);
            expect(vm.methodDesc).toEqual(null);
            expect(vm.projectUrl).toEqual(null);
            expect(vm.publicationUrl).toEqual(null);
            expect(vm.subErrors.msg).toEqual(errorResponse.error);
            expect(vm.stopLoader).toHaveBeenCalled();
        });
    });

    describe('Unit tests for sortFunction function', function () {
        it('sort column by is known', function () {
            var return_value = vm.sortFunction({});
            expect(return_value).not.toEqual(0);
        });

        it('sort column by is not known', function () {
            vm.sortColumn = 'notKnown';
            var return_value = vm.sortFunction({});
            expect(return_value).toEqual(0);
        });
    });

    describe('Unit tests for sortLeaderboard function', function () {
        it('column index is null and passed `column` not same with the current `sortColumn`', function () {
            vm.sortLeaderboard(vm, 'number', null);
            expect(vm.reverseSort).toEqual(false);
        });

        it('column index is null and passed `column` same with the current `sortColumn`', function () {
            vm.sortLeaderboard(vm, 'rank', null);
            expect(vm.reverseSort).toEqual(true);
        });

        it('column index is not null and passed `column` and `index` not same with the current `sortColumn` and `columnIndexSort`', function () {
            vm.sortLeaderboard(vm, 'number', 1);
            expect(vm.reverseSort).toEqual(false);
            expect(vm.columnIndexSort).toEqual(1);
        });

        it('column index is not null and passed `column` and `index` same with the current `sortColumn` and `columnIndexSort`', function () {
            vm.sortLeaderboard(vm, 'rank', 0);
            expect(vm.reverseSort).toEqual(true);
            expect(vm.columnIndexSort).toEqual(0);
        });
    });

    describe('Unit tests for getLeaderboard function \
        `jobs/challenge_phase_split/<phase_split_id>/leaderboard/?page_size=1000`', function () {
        var success, successResponse, errorResponse;

        beforeEach(function () {
            spyOn($interval, 'cancel');
            spyOn(vm, 'startLoader');
            spyOn(vm, 'stopLoader');
            spyOn(vm, 'startLeaderboard');

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

        it('successfully get the leaderboard', function () {
            success = true;
            successResponse = {
                results: {
                    duration: 'year',
                    results: [
                        {
                            id: 1,
                            submission__submitted_at: (new Date() - new Date().setFullYear(new Date().getFullYear() - 1)),
                        },
                    ]
                },
            };
            var phaseSplitId = 1;
            vm.getLeaderboard(phaseSplitId);
            vm.stopLeaderboard();
            expect($interval.cancel).toHaveBeenCalled();
            expect(vm.isResult).toEqual(true);
            expect(vm.startLoader).toHaveBeenCalledWith('Loading Leaderboard Items');
            expect(vm.leaderboard).toEqual(successResponse.results);

            expect(vm.phaseName).toEqual(vm.phaseSplitId);
            expect(vm.startLeaderboard).toHaveBeenCalled();
            expect(vm.stopLoader).toHaveBeenCalled();
        });

        it('backend error', function () {
            success = false;
            errorResponse = 'error';
            var phaseSplitId = 1;
            vm.getLeaderboard(phaseSplitId);
            vm.stopLeaderboard();
            expect($interval.cancel).toHaveBeenCalled();
            expect(vm.isResult).toEqual(true);
            expect(vm.startLoader).toHaveBeenCalledWith('Loading Leaderboard Items');
            expect(vm.leaderboard.error).toEqual(errorResponse);
            expect(vm.stopLoader).toHaveBeenCalled();
        });
    });

    describe('Unit tests for getResults function', function () {
        var submissionCountSuccess, submissionListSuccess, successResponse, errorResponse;
        var submission_list = [
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
            spyOn($interval, 'cancel');
            spyOn(vm, 'startLoader');
            spyOn(vm, 'stopLoader');
            spyOn($rootScope, 'notify');
            spyOn($state, 'go');
            spyOn(utilities, 'storeData');

            vm.challengeId = 1;
            vm.phases = {
                results: [
                    {
                        id: 1,
                        name: "Challenge phase name",
                        description: "Challenge phase description",
                        leaderboard_public: true
                    },
                ]
            };

            utilities.sendRequest = function (parameters) {
                if ((submissionCountSuccess == true && parameters.url == "analytics/challenge/" + vm.challengeId + "/challenge_phase/" + vm.phaseId + "/count") ||
                (submissionListSuccess == true && parameters.url == "jobs/challenge/" + vm.challengeId + "/challenge_phase/" + vm.phaseId + "/submission/")) {
                    parameters.callback.onSuccess({
                        data: successResponse
                    });
                } else if ((submissionCountSuccess == false && parameters.url == "analytics/challenge/" + vm.challengeId + "/challenge_phase/" + vm.phaseId + "/count") ||
                (submissionListSuccess == false && parameters.url == "jobs/challenge/" + vm.challengeId + "/challenge_phase/" + vm.phaseId + "/submission/")){
                    parameters.callback.onError({
                        data: errorResponse
                    });
                }
            };
        });

        it('get the leaderboard of the current phase', function () {
            submissionCountSuccess = null;
            submissionListSuccess = null;
            var phaseId = 1;
            vm.getResults(phaseId);
            vm.stopFetchingSubmissions();
            expect($interval.cancel).toHaveBeenCalled();
            expect(vm.isResult).toEqual(true);
            expect(vm.phaseId).toEqual(phaseId);

            expect(vm.currentPhaseLeaderboardPublic).toEqual(true);
        });

        it('get the submission count \
            `analytics/challenge/<challenge_id>/challenge_phase/<phase_id>/count`', function () {
            submissionCountSuccess = true;
            submissionListSuccess = null;
            var phaseId = 1;
            successResponse = {
                challenge_phase: 1,
                participant_team_submission_count: 200
            };
            vm.getResults(phaseId);
            expect(vm.submissionCount).toEqual(successResponse.participant_team_submission_count);
        });

        it('backend error on getting submission count \
            `analytics/challenge/<challenge_id>/challenge_phase/<phase_id>/count`', function () {
            submissionCountSuccess = false;
            submissionListSuccess = null;
            var phaseId = 1;
            errorResponse = 'error';
            vm.getResults(phaseId);
            expect($rootScope.notify).toHaveBeenCalledWith("error", errorResponse);
        });

        submission_list.forEach(response => {
            it('get submissions of a particular challenge phase when pagination next is ' + response.next + ' \
                and previous is ' + response.previous + '`jobs/challenge/<challenge_id>/challenge_phase/<phase_id>/submission/`', function () {
                submissionListSuccess = true;
                var phaseId = 1;
                successResponse = response;
                successResponse.results = [
                    {
                        id: 1,
                        participant_team: "Participant team",
                        challenge_phase: "Challenge phase",
                        is_public: true,
                        is_baseline: true
                    }
                ];

                vm.getResults(phaseId);
                expect(vm.isExistLoader).toBeTruthy();
                expect(vm.startLoader).toHaveBeenCalledWith("Loading Submissions");
                for (var i = 0; i < successResponse.results.length; i++){
                    expect(vm.submissionVisibility[successResponse.results[i].id]).toEqual(successResponse.results[i].is_public);
                    expect(vm.baselineStatus[successResponse.results[i].id] = successResponse.results[i].is_baseline);
                }
                expect(vm.submissionResult).toEqual(successResponse);

                if (vm.submissionResult.next == null) {
                    expect(vm.isNext).toEqual('disabled');
                    expect(vm.currentPage).toEqual(1);
                } else {
                    expect(vm.isNext).toEqual('');
                    expect(vm.currentPage).toEqual(vm.submissionResult.next.split('page=')[1] - 1);
                }

                if (vm.submissionResult.previous == null) {
                    expect(vm.isPrev).toEqual('disabled');
                } else {
                    expect(vm.isPrev).toEqual('');
                }

                if (vm.submissionResult.next !== null) {
                    expect(vm.currentPage).toEqual(vm.submissionResult.next.split('page=')[1] - 1);
                } else {
                    expect(vm.currentPage).toEqual(1);
                }
            });
        });

        it('backend error on getting submissions of a particular challenge \
            `jobs/challenge/<challenge_id>/challenge_phase/<phase_id>/submission/`', function () {
            submissionListSuccess = false;
            submissionCountSuccess = null;
            var phaseId = 1;
            errorResponse = {
                detail: 'error'
            };
            vm.getResults(phaseId);
            expect(utilities.storeData).toHaveBeenCalledWith("emailError", errorResponse.detail);
            expect($state.go).toHaveBeenCalledWith('web.permission-denied');
            expect(vm.stopLoader).toHaveBeenCalled();
        });

        it('to load data with pagination `load` function', function () {
            submissionListSuccess = true;
            submissionCountSuccess = null;
            var phaseId = 1;
            successResponse = {
                results: [
                    {
                        id: 1,
                        participant_team: "Participant team",
                        challenge_phase: "Challenge phase",
                        is_public: true,
                        is_baseline: true
                    }
                ],
                // get submissions response
                next: "page=4",
                previous: "page=2",
            };      
            vm.getResults(phaseId);
            spyOn($http, 'get').and.callFake(function () {
                var deferred = $injector.get('$q').defer();
                return deferred.promise;
            });
            var url = 'challenge/<challenge_id>/submission/page=2';
            vm.load(url);
            expect(vm.isExistLoader).toBeTruthy();
            expect(vm.startLoader).toHaveBeenCalledWith("Loading Submissions");
            var headers = {
                'Authorization': "Token " + utilities.getData('userKey')
            };
            expect($http.get).toHaveBeenCalledWith(url, {headers: headers});
        });
    });

    describe('Unit tests for refreshSubmissionData function \
        `jobs/challenge/<challenge_id>/challenge_phase/<phase_id>/submission/?page=`', function () {
        var success, successResponse;
        var errorResponse = 'error';
        var results = [
            {
                id: 1,
                is_public: true,
                is_baseline: true
            },
            {
                id: 2,
                is_public: false,
                is_baseline: true
            }
        ];
        var paginated_list = [
            {
                count: 0,
                next: null,
                previous: null,
                results: results
            },
            {
                count: 2,
                next: null,
                previous: null,
                results: results
            },
            {
                count: 30,
                next: 'page=5',
                previous: null,
                results: results
            },
            {
                count: 30,
                next: null,
                previous: 'page=3',
                results: results
            },
            {
                count: 30,
                next: 'page=4',
                previous: 'page=2',
                results: results
            }
        ];

        beforeEach(function () {
            spyOn(vm, 'startLoader');
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

        paginated_list.forEach(response => {
            it('submission data list have count' + response.count + ', next ' + response.next + 'and previous ' + response.previous, function () {
                success = true;
                successResponse = response;
                vm.refreshSubmissionData();
                expect(vm.isResult).toEqual(false);
                expect(vm.startLoader).toHaveBeenCalledWith("Loading Submissions");
                expect(vm.submissionResult).toEqual(successResponse);

                if (response.count == 0) {
                    expect(vm.showPagination).toEqual(false);
                    expect(vm.paginationMsg).toEqual("No results found");
                } else {
                    expect(vm.showPagination).toEqual(true);
                    expect(vm.paginationMsg).toEqual("");
                }

                if (response.next == null) {
                    expect(vm.isNext).toEqual('disabled');
                } else {
                    expect(vm.isNext).toEqual('');
                }

                if (response.previous == null) {
                    expect(vm.isPrev).toEqual('disabled');
                } else {
                    expect(vm.isPrev).toEqual('');
                }

                if (response.next != null) {
                    expect(vm.currentPage).toEqual(response.next.split('page=')[1] - 1);
                } else {
                    expect(vm.currentPage).toEqual(1);
                }

                for (var i = 0; i < response.results.length; i++) {
                    expect(vm.submissionVisibility[response.results[i].id]).toEqual(response.results[i].is_public);
                    expect(vm.baselineStatus[response.results[i].id]).toEqual(response.results[i].is_baseline);
                }

                expect(vm.showUpdate).toEqual(false);
                expect(vm.stopLoader).toHaveBeenCalled();
            });
        });

        it('backend error', function () {
            success = false;
            vm.refreshSubmissionData();
            expect(vm.stopLoader).toHaveBeenCalled();
        });
    });

    describe('Unit tests for refreshLeaderboard function \
        `jobs/challenge_phase_split/<phase_split_id>/leaderboard/?page_size=1000`', function () {
        var success, successResponse, errorResponse;

        beforeEach(function () {
            spyOn(vm, 'startLoader');
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

        it('on success of the function', function () {
            success = true;
            successResponse = {
                results: 'success'
            };
            vm.refreshLeaderboard();
            expect(vm.startLoader).toHaveBeenCalledWith("Loading Leaderboard Items");
            expect(vm.leaderboard).toEqual(successResponse.results);
            expect(vm.stopLoader).toHaveBeenCalled();
        });

        it('backend error', function () {
            success = false;
            errorResponse = 'error';
            vm.refreshLeaderboard();
            expect(vm.startLoader).toHaveBeenCalledWith("Loading Leaderboard Items");
            expect(vm.leaderboard.error).toEqual(errorResponse);
            expect(vm.stopLoader).toHaveBeenCalled();
        });
    });

    describe('Unit tests for createNewTeam function \
        `participants/participant_team`', function () {
        var success, successResponse;
        var errorResponse = {
            team_name: ['error']
        };
        var team_name_list = [
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
            spyOn(vm, 'startLoader');
            spyOn(vm, 'stopLoader');
            spyOn(angular, 'element');
            spyOn($rootScope, 'notify');
            vm.team.name = "team_name";
            vm.team.url = "team_url";

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

        team_name_list.forEach(response => {
            it('when pagination next is ' + response.next + 'and previous is ' + response.previous, function () {
                success = true;
                successResponse = response;
                vm.createNewTeam();
                expect(vm.isLoader).toEqual(true);
                expect(vm.loaderTitle).toEqual('');
                expect(angular.element).toHaveBeenCalledWith('.new-team-card');
                expect(vm.startLoader("Loading Teams"));
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

        it('backend error', function () {
            success = false;
            vm.createNewTeam();
            expect(vm.isLoader).toEqual(true);
            expect(vm.loaderTitle).toEqual('');
            expect(angular.element).toHaveBeenCalledWith('.new-team-card');
            expect(vm.startLoader("Loading Teams"));
            expect(vm.team.error).toEqual(errorResponse.team_name[0]);
            expect(vm.stopLoader).toHaveBeenCalled();
            expect($rootScope.notify).toHaveBeenCalledWith("error", "New team couldn't be created.");
        });
    });

    describe('Unit tests for getAllSubmissionResults function \
        `challenges/<challenge_id>/challenge_phase/<phase_id>/submissions`', function() {
        var success, successResponse;
        var errorResponse = {
            detail: 'error'
        };
        var submission_list = [
            {
                count: 0,
                next: null,
                previous: null,
            },
            {
                count: 2,
                next: null,
                previous: null,
            },
            {
                count: 30,
                next: 'page=5',
                previous: null,
            },
            {
                count: 30,
                next: null,
                previous: 'page=3',
            },
            {
                count: 30,
                next: 'page=4',
                previous: 'page=2',
            }
        ];

        beforeEach(function () {
            spyOn(vm, 'startLoader');
            spyOn(vm, 'stopLoader');
            spyOn(angular, 'element');
            spyOn($interval, 'cancel');
            spyOn(utilities, 'storeData');
            spyOn($state, 'go');

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

        submission_list.forEach(response => {
            it('submission list have count' + response.count + ', next ' + response.next + 'and previous ' + response.previous, function() {
                success = true;
                successResponse = response;
                var phaseId = 1
                vm.getAllSubmissionResults(phaseId);
                vm.stopFetchingSubmissions();
                expect($interval.cancel).toHaveBeenCalled();
                expect(vm.isResult).toEqual(true);
                expect(vm.phaseId).toEqual(phaseId);

                expect(vm.submissionResult).toEqual(response);
                if (vm.submissionResult.count == 0) {
                    expect(vm.showPagination).toEqual(false);
                    expect(vm.paginationMsg).toEqual("No results found");
                } else {
                    expect(vm.showPagination).toEqual(true);
                    expect(vm.paginationMsg).toEqual("");
                }

                if (vm.submissionResult.next == null) {
                    expect(vm.isNext).toEqual('disabled');
                } else {
                    expect(vm.isNext).toEqual('');

                }
                if (vm.submissionResult.previous == null) {
                    expect(vm.isPrev).toEqual('disabled');
                } else {
                    expect(vm.isPrev).toEqual('');
                }
                if (vm.submissionResult.next != null) {
                    expect(vm.currentPage).toEqual(vm.submissionResult.next.split('page=')[1] - 1);
                } else {
                    expect(vm.currentPage).toEqual(1);
                }

                expect(vm.stopLoader).toHaveBeenCalled();
            });
        });

        it('backend error', function () {
            success = false;
            var phaseId = 1
            vm.getAllSubmissionResults(phaseId);
            vm.stopFetchingSubmissions();
            expect($interval.cancel).toHaveBeenCalled();
            expect(vm.isResult).toEqual(true);
            expect(vm.phaseId).toEqual(phaseId);

            expect(utilities.storeData).toHaveBeenCalledWith('emailError', errorResponse.detail);
            expect($state.go).toHaveBeenCalledWith('web.permission-denied');
            expect(vm.stopLoader).toHaveBeenCalled();
        });
    });

    describe('Unit tests for changeSubmissionVisibility function \
        `jobs/challenge/<challenge_id>/challenge_phase/<phase_id>/submission/<submission_id>`', function () {
        var success;

        beforeEach(function () {
            utilities.sendRequest = function (parameters) {
                if (success) {
                    parameters.callback.onSuccess({
                        data: 'success',
                    });
                } else {
                    parameters.callback.onError({
                        data: 'error'
                    });
                }
            };
        });

        it('change submission visibility', function () {
            var submissionId = 1;
            expect(vm.submissionVisibility).toEqual({});
            vm.submissionVisibility[1] = true;
            vm.changeSubmissionVisibility(submissionId);
            expect(vm.submissionVisibility[submissionId]).toEqual(true);
        });
    });

    describe('Unit tests for changeBaselineStatus function \
        `jobs/challenge/<challenge_id>/challenge_phase/<phase_id>/submission/<submission_id>`', function () {
        var success;

        beforeEach(function () {
            utilities.sendRequest = function (parameters) {
                if (success) {
                    parameters.callback.onSuccess({
                        data: 'success',
                    });
                } else {
                    parameters.callback.onError({
                        data: 'error'
                    });
                }
            };
        });

        it('change Baseline Status', function () {
            var submissionId = 1;
            expect(vm.baselineStatus).toEqual({});
            vm.baselineStatus[1] = true;
            vm.changeBaselineStatus(submissionId);
            expect(vm.baselineStatus[submissionId]).toEqual(true);
        });
    });

    describe('Unit tests for showRemainingSubmissions function \
        `jobs/<challenge_id>/remaining_submissions`', function () {
        var success, successResponse;
        var errorResponse = {
            error: 'error'
        }

        beforeEach(function () {
            jasmine.clock().install;
            spyOn(vm, 'startLoader');
            spyOn(vm, 'stopLoader');
            spyOn($rootScope, 'notify');

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

        afterEach(function () {
            jasmine.clock().uninstall();
        });

        it('when submission limit exceeded', function () {
            success = true;
            successResponse = {
                phases: {
                    first_object: {
                        id: undefined,
                        limits: {
                            submission_limit_exceeded: true,
                            remaining_submissions_today_count: 0,
                            remaining_time: 0,
                            message: "Max Limit Exceeded",
                        }
                    },
                }
            };
            vm.showRemainingSubmissions();
            expect(vm.maxExceeded).toEqual(true);
            expect(vm.maxExceededMessage).toEqual(successResponse.phases.first_object.limits.message);
        });

        it('when today remaining submission greater than 0', function () {
            success = true;
            successResponse = {
                phases: {
                    first_object: {
                        id: undefined,
                        limits: {
                            submission_limit_exceeded: false,
                            remaining_submissions_today_count: 10,
                            remaining_time: 0,
                        }
                    }
                }
            };
            vm.showRemainingSubmissions();
            expect(vm.remainingSubmissions).toEqual(successResponse.phases.first_object.limits);
            expect(vm.showSubmissionNumbers).toEqual(true);
        });

        it('countdown for the remaining timer', function () {
            success = true;
            successResponse = {
                phases: {
                    first_object: {
                        id: undefined,
                        limits: {
                            submission_limit_exceeded: false,
                            remaining_submissions_today_count: 0,
                            remaining_time: 36000,
                        }
                    }
                }
            };
            vm.showRemainingSubmissions();
            expect(vm.message).toEqual(successResponse.phases.first_object.limits);
            expect(vm.showClock).toEqual(true);

            expect(vm.remainingTime).toEqual(successResponse.phases.first_object.limits.remaining_time);
            expect(vm.days).toEqual(Math.floor(vm.remainingTime / 24 / 60 / 60));
            expect(vm.hoursLeft).toEqual(Math.floor((vm.remainingTime) - (vm.days * 86400)));
            expect(vm.hours).toEqual(Math.floor(vm.hoursLeft / 3600));
            expect(vm.minutesLeft).toEqual(Math.floor((vm.hoursLeft) - (vm.hours * 3600)));
            expect(vm.minutes).toEqual(Math.floor(vm.minutesLeft / 60));
        });

        it('backend error', function () {
            success = false;
            vm.showRemainingSubmissions();
            expect(vm.stopLoader).toHaveBeenCalled();
            expect($rootScope.notify).toHaveBeenCalledWith("error", errorResponse.error);
        });
    });

    describe('Unit tests for showMdDialog', function () {
        it('Variables initialized', function () {
            vm.submissionResult = [];
            vm.submissionMetaData = {
                id: 1,
                method_name: 'method name',
                method_description: 'method description',
                project_url: 'project url',
                publication_url: 'publication url'
            };
            var submissionId = 1;
            var ev = new Event('click');
            var $mdDialog = $injector.get('$mdDialog');
            var $mdDialogOpened = false;
            $mdDialog.show = jasmine.createSpy().and.callFake(function () {
                $mdDialogOpened = true;
            });

            vm.showMdDialog(ev, submissionId);
            expect(vm.method_name).toEqual(vm.submissionMetaData.method_name);
            expect(vm.method_description).toEqual(vm.submissionMetaData.method_description);
            expect(vm.project_url).toEqual(vm.submissionMetaData.project_url);
            expect(vm.publication_url).toEqual(vm.submissionMetaData.publication_url);
            expect(vm.submissionId).toEqual(submissionId);

            expect($mdDialog.show).toHaveBeenCalled();
            expect($mdDialogOpened).toBe(true);
        });
    });

    describe('Unit tests for updateSubmissionMetaData function \
        `jobs/challenge/<challenge_id>/challenge_phase/<phase_id>/submission/<submission_id>`', function () {
        var success;
        var errorResponse = 'error';

        beforeEach(function () {
            spyOn($mdDialog, 'hide');
            spyOn($rootScope, 'notify');

            utilities.sendRequest = function (parameters) {
                if (success) {
                    parameters.callback.onSuccess({
                        data: 'success',
                        status: 200
                    });
                } else {
                    parameters.callback.onError({
                        data: errorResponse
                    });
                }
            };
        });

        it('valid form submission and succesfully updated form', function () {
            vm.method_name = 'method name';
            vm.method_description = 'method description';
            vm.project_url = 'project url';
            vm.publication_url = 'publication url';
            success = true;
            var updateSubmissionMetaDataForm = true;
            vm.updateSubmissionMetaData(updateSubmissionMetaDataForm);
            expect(status).toBeDefined();
            expect($mdDialog.hide).toHaveBeenCalled();
            expect($rootScope.notify).toHaveBeenCalledWith("success", "The data is successfully updated!");
        });

        it('valid form submission and backend error', function () {
            vm.method_name = 'method name';
            vm.method_description = 'method description';
            vm.project_url = 'project url';
            vm.publication_url = 'publication url';
            success = false;
            var updateSubmissionMetaDataForm = true;
            vm.updateSubmissionMetaData(updateSubmissionMetaDataForm);
            expect($mdDialog.hide).toHaveBeenCalled();
            expect($rootScope.notify).toHaveBeenCalledWith("error", errorResponse);
        });

        it('invalid form submission', function () {
            var updateSubmissionMetaDataForm = false;
            vm.updateSubmissionMetaData(updateSubmissionMetaDataForm);
            expect($mdDialog.hide).toHaveBeenCalled();
        });
    });

    describe('Unit tests for isStarred function \
        `challenges/<challenge_id>/`', function () {
        var success, successResponse;

        beforeEach(function () {
            utilities.sendRequest = function (parameters) {
                if (success) {
                    parameters.callback.onSuccess({
                        data: successResponse
                    });
                } else {
                    parameters.callback.onError({
                        data: 'error'
                    });
                }
            };
        });

        it('get the stars count and user specific unstarred', function () {
            success = true;
            successResponse = {
                count: 1,
                is_starred: false
            };
            vm.isStarred();
            expect(vm.count).toEqual(successResponse.count);
            expect(vm.is_starred).toEqual(successResponse.is_starred);
            expect(vm.caption).toEqual('Star');
        });

        it('get the stars count and user specific starred', function () {
            success = true;
            successResponse = {
                count: 1,
                is_starred: true
            };
            vm.isStarred();
            expect(vm.count).toEqual(successResponse.count);
            expect(vm.is_starred).toEqual(successResponse.is_starred);
            expect(vm.caption).toEqual('Unstar');
        });
    });

    describe('Unit tests for starChallenge function \
        `challenges/<challenge_id>/`', function () {
        var success, successResponse;
        var errorResponse = 'error';

        beforeEach(function () {
            spyOn($rootScope, 'notify');

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

        it('Unstar the challenge', function () {
            success = true;
            successResponse = {
                count: 10,
                is_starred: true
            };
            vm.starChallenge();
            expect(vm.count).toEqual(successResponse.count);
            expect(vm.is_starred).toEqual(successResponse.is_starred);
            expect(vm.caption).toEqual('Unstar');
        });

        it('Star the challenge', function () {
            success = true;
            successResponse = {
                count: 10,
                is_starred: false
            };
            vm.starChallenge();
            expect(vm.count).toEqual(successResponse.count);
            expect(vm.is_starred).toEqual(successResponse.is_starred);
            expect(vm.caption).toEqual('Star');
        });

        it('backend error', function () {
            success = false;
            vm.starChallenge();
            expect($rootScope.notify).toHaveBeenCalledWith("error", errorResponse);
        });
    });

    describe('Unit tests for overviewDialog function', function () {
        it('open dialog for edit challenge overview', function () {
            var $mdDialog = $injector.get('$mdDialog');
            var $mdDialogOpened = false;
            $mdDialog.show = jasmine.createSpy().and.callFake(function () {
                $mdDialogOpened = true;
            });

            vm.overviewDialog();
            expect($mdDialog.show).toHaveBeenCalled();
            expect($mdDialogOpened).toEqual(true);
        });
    });

    describe('Unit tests for editChallengeOverview function \
        `challenges/challenge_host_team/<challenge_host_id>/challenge/<challenge_id>`', function () {
        var success;
        var errorResponse = 'error';

        beforeEach(function () {
            spyOn(utilities, 'getData');
            spyOn($mdDialog, 'hide');
            spyOn($rootScope, 'notify');

            utilities.sendRequest = function (parameters) {
                if (success) {
                    parameters.callback.onSuccess({
                        status: 200
                    });
                } else {
                    parameters.callback.onError({
                        data: errorResponse
                    });
                }
            };
        });

        it('valid editchallengeoverview form and succesfull edit', function () {
            var editChallengeOverviewForm = true;
            success = true;
            vm.page.description = "description";
            vm.editChallengeOverview(editChallengeOverviewForm);
            expect(utilities.getData).toHaveBeenCalledWith("challengeCreator");
            expect($mdDialog.hide).toHaveBeenCalled();
            expect($rootScope.notify).toHaveBeenCalledWith("success", "The description is successfully updated!");
        });

        it('valid editchallengeoverview form and backend error', function () {
            var editChallengeOverviewForm = true;
            success = false;
            vm.tempDesc = "temp description";
            vm.page.description = "description";
            vm.editChallengeOverview(editChallengeOverviewForm);
            expect(utilities.getData).toHaveBeenCalledWith("challengeCreator");
            expect($mdDialog.hide).toHaveBeenCalled();
            expect(vm.page.description).toEqual(vm.tempDesc);
            expect($rootScope.notify).toHaveBeenCalledWith('error', errorResponse);
        });

        it('invalid editchallengeoverview form', function () {
            var editChallengeOverviewForm = false;
            vm.tempDesc = "No description";
            vm.page.description = "description";
            vm.editChallengeOverview(editChallengeOverviewForm);
            expect(vm.page.description).toEqual(vm.tempDesc);
            expect($mdDialog.hide).toHaveBeenCalled();
        });
    });

    describe('Unit tests for deleteChallengeDialog function', function () {
        it('open dialog for delete challenge', function () {
            var $mdDialog = $injector.get('$mdDialog');
            var $mdDialogOpened = false;
            $mdDialog.show = jasmine.createSpy().and.callFake(function () {
                $mdDialogOpened = true;
            });

            vm.deleteChallengeDialog();
            expect(vm.titleInput).toEqual("");
            expect($mdDialog.show).toHaveBeenCalled();
            expect($mdDialogOpened).toEqual(true);
        });
    });

    describe('Unit tests for deleteChallenge function \
        `challenges/challenge/<challenge_id>/disable`', function () {
        var success;
        var errorResponse = 'error';

        beforeEach(function () {
            spyOn($mdDialog, 'hide');
            spyOn($rootScope, 'notify');

            utilities.sendRequest = function (parameters) {
                if (success) {
                    parameters.callback.onSuccess({
                        status: 204
                    });
                } else {
                    parameters.callback.onError({
                        data: errorResponse
                    });
                }
            };
        });

        it('valid delete challenge form & successfully delete challenge', function () {
            var deleteChallengeForm = true;
            success = true;
            vm.deleteChallenge(deleteChallengeForm);
            expect($mdDialog.hide).toHaveBeenCalled();
            expect($rootScope.notify).toHaveBeenCalledWith("success", "The Challenge is successfully deleted!");
        });

        it('valid delete challenge form & backend error', function () {
            var deleteChallengeForm = true;
            success = false;
            vm.deleteChallenge(deleteChallengeForm);
            expect($mdDialog.hide).toHaveBeenCalled();
            expect($rootScope.notify).toHaveBeenCalledWith("error", errorResponse);
        });

        it('invalid delete challenge form', function () {
            var deleteChallengeForm = false;
            vm.deleteChallenge(deleteChallengeForm);
            expect($mdDialog.hide).toHaveBeenCalled();
        });
    });

    describe('Unit tests for submissionGuidelinesDialog function', function () {
        it('open dialog to `edit submission guidelines`', function () {
            var $mdDialog = $injector.get('$mdDialog');
            var $mdDialogOpened = false;
            $mdDialog.show = jasmine.createSpy().and.callFake(function () {
                $mdDialogOpened = true;
            });

            vm.page.submission_guidelines = "submission guidelines";
            vm.submissionGuidelinesDialog();
            expect(vm.tempSubmissionGuidelines).toEqual(vm.page.submission_guidelines);
            expect($mdDialog.show).toHaveBeenCalled();
            expect($mdDialogOpened).toEqual(true);
        });
    });

    describe('Unit tests for editSubmissionGuideline function \
        `challenges/challenge_host_team/<challenge_host_id>/challenge/<challenge_id>`', function () {
        var success;
        var errorResponse = 'error';

        beforeEach(function () {
            spyOn(utilities, 'getData');
            spyOn($mdDialog, 'hide');
            spyOn($rootScope, 'notify');

            utilities.sendRequest = function (parameters) {
                if (success) {
                    parameters.callback.onSuccess({
                        status: 200
                    });
                } else {
                    parameters.callback.onError({
                        data: errorResponse
                    });
                }
            };
        });

        it('valid edit submission guidelines form & successfull edit', function () {
            var editSubmissionGuidelinesForm = true;
            success = true;
            vm.page.submission_guidelines = "submission guidelines";
            vm.editSubmissionGuideline(editSubmissionGuidelinesForm);
            expect(utilities.getData).toHaveBeenCalledWith("challengeCreator");
            expect($mdDialog.hide).toHaveBeenCalled();
            expect($rootScope.notify).toHaveBeenCalledWith("success", "The submission guidelines is successfully updated!");
        });

        it('valid edit submission guidelines form & backend error', function () {
            var editSubmissionGuidelinesForm = true;
            success = false;
            vm.tempSubmissionGuidelines = "temp submission guidelines";
            vm.page.submission_guidelines = "submission guidelines";
            vm.editSubmissionGuideline(editSubmissionGuidelinesForm);
            expect(utilities.getData).toHaveBeenCalledWith("challengeCreator");
            expect($mdDialog.hide).toHaveBeenCalled();
            expect(vm.page.submission_guidelines).toEqual(vm.tempSubmissionGuidelines);
            expect($rootScope.notify).toHaveBeenCalledWith("error", errorResponse);
        });

        it('invalid edit submission guidelines form', function () {
            var editSubmissionGuidelinesForm = false;
            vm.tempSubmissionGuidelines = "temp submission guidelines";
            vm.page.submission_guidelines = "submission guidelines";
            vm.editSubmissionGuideline(editSubmissionGuidelinesForm);
            expect(vm.page.submission_guidelines).toEqual(vm.tempSubmissionGuidelines);
            expect($mdDialog.hide).toHaveBeenCalled();
        });
    });

    describe('Unit tests for evaluationCriteriaDialog function', function () {
        it('open dialog to `edit evaluation criteria`', function () {
            var $mdDialog = $injector.get('$mdDialog');
            var $mdDialogOpened = false;
            $mdDialog.show = jasmine.createSpy().and.callFake(function () {
                $mdDialogOpened = true;
            });

            vm.page.evaluation_details = "evaluation details";
            vm.evaluationCriteriaDialog();
            expect(vm.tempEvaluationCriteria).toEqual(vm.page.evaluation_details);
            expect($mdDialog.show).toHaveBeenCalled();
            expect($mdDialogOpened).toEqual(true);
        });
    });

    describe('Unit tests for editEvaluationCriteria function \
        `challenges/challenge_host_team/<challenge_host_id>/challenge/<challenge_id>`', function () {
        var success;
        var errorResponse = 'error';

        beforeEach(function () {
            spyOn(utilities, 'getData');
            spyOn($mdDialog, 'hide');
            spyOn($rootScope, 'notify');

            utilities.sendRequest = function (parameters) {
                if (success) {
                    parameters.callback.onSuccess({
                        status: 200
                    });
                } else {
                    parameters.callback.onError({
                        data: errorResponse
                    });
                }
            };
        });

        it('valid `edit evaluation criteria` form & successfull edit', function () {
            var editEvaluationCriteriaForm = true;
            success = true;
            vm.page.evaluation_details = "evaluation details";
            vm.editEvaluationCriteria(editEvaluationCriteriaForm);
            expect(utilities.getData).toHaveBeenCalledWith("challengeCreator");
            expect($mdDialog.hide).toHaveBeenCalled();
            expect($rootScope.notify).toHaveBeenCalledWith("success", "The evaluation details is successfully updated!");
        });

        it('valid `edit evaluation criteria` form & backend error', function () {
            var editEvaluationCriteriaForm = true;
            success = false;
            vm.tempEvaluationCriteria = "temp evaluation details";
            vm.page.evaluation_details = "evaluation details";
            vm.editEvaluationCriteria(editEvaluationCriteriaForm);
            expect(utilities.getData).toHaveBeenCalledWith("challengeCreator");
            expect($mdDialog.hide).toHaveBeenCalled();
            expect(vm.page.evaluation_details).toEqual(vm.tempEvaluationCriteria);
            expect($rootScope.notify).toHaveBeenCalledWith("error", errorResponse);
        });

        it('invalid `edit evaluation criteria` form', function () {
            var editEvaluationCriteriaForm = false;
            vm.tempEvaluationCriteria = "temp evaluation details";
            vm.page.evaluation_details = "evaluation details";
            vm.editEvaluationCriteria(editEvaluationCriteriaForm);
            expect(vm.page.evaluation_details).toEqual(vm.tempEvaluationCriteria);
            expect($mdDialog.hide).toHaveBeenCalled();
        });
    });

    describe('Unit tests for evaluationScriptDialog function', function () {
        it('open dialog to `edit evaluation script`', function () {
            var $mdDialog = $injector.get('$mdDialog');
            var $mdDialogOpened = false;
            $mdDialog.show = jasmine.createSpy().and.callFake(function () {
                $mdDialogOpened = true;
            });

            vm.evaluationScriptDialog();
            expect($mdDialog.show).toHaveBeenCalled();
            expect($mdDialogOpened).toEqual(true);
        });
    });

    describe('Unit tests for editEvalScript function \
        `challenges/challenge_host_team/<challenge_host_id>/challenge/<challenge_id>`', function () {
        var success;
        var errorResponse = 'error';

        beforeEach(function () {
            spyOn(utilities, 'getData');
            spyOn($mdDialog, 'hide');
            spyOn($rootScope, 'notify');

            utilities.sendRequest = function (parameters) {
                if (success) {
                    parameters.callback.onSuccess({
                        status: 200
                    });
                } else {
                    parameters.callback.onError({
                        data: errorResponse
                    });
                }
            };
        });

        it('valid `edit evaluation script` form & successfull edit', function () {
            var editEvaluationScriptForm = true;
            success = true;
            vm.page.evaluation_details = "evaluation details";
            vm.editEvalScript(editEvaluationScriptForm);
            expect(utilities.getData).toHaveBeenCalledWith("challengeCreator");
            expect($mdDialog.hide).toHaveBeenCalled();
            expect($rootScope.notify).toHaveBeenCalledWith("success", "The evaluation script is successfully updated!");
        });

        it('valid `edit evaluation script` form & backend error', function () {
            var editEvaluationScriptForm = true;
            success = false;
            vm.tempEvaluationCriteria = "temp evaluation details";
            vm.page.evaluation_details = "evaluation details";
            vm.editEvalScript(editEvaluationScriptForm);
            expect(utilities.getData).toHaveBeenCalledWith("challengeCreator");
            expect($mdDialog.hide).toHaveBeenCalled();
            expect(vm.page.evaluation_details).toEqual(vm.tempEvaluationCriteria);
            expect($rootScope.notify).toHaveBeenCalledWith("error", errorResponse);
        });

        it('invalid `edit evaluation script` form', function () {
            var editEvaluationScriptForm = false;
            vm.tempEvaluationCriteria = "temp evaluation details";
            vm.page.evaluation_details = "evaluation details";
            vm.editEvalScript(editEvaluationScriptForm);
            expect(vm.page.evaluation_details).toEqual(vm.tempEvaluationCriteria);
            expect($mdDialog.hide).toHaveBeenCalled();
        });
    });

    describe('Unit tests for termsAndConditionsDialog function', function () {
        it('open dialog to `terms and conditions`', function () {
            var $mdDialog = $injector.get('$mdDialog');
            var $mdDialogOpened = false;
            $mdDialog.show = jasmine.createSpy().and.callFake(function () {
                $mdDialogOpened = true;
            });

            vm.page.terms_and_conditions = "terms and conditions";
            vm.termsAndConditionsDialog();
            expect(vm.tempTermsAndConditions).toEqual(vm.page.terms_and_conditions);
            expect($mdDialog.show).toHaveBeenCalled();
            expect($mdDialogOpened).toEqual(true);
        });
    });

    describe('Unit tests for editTermsAndConditions function \
        `challenges/challenge_host_team/<challenge_host_id>/challenge/<challenge_id>`', function () {
        var success;
        var errorResponse = 'error';

        beforeEach(function () {
            spyOn(utilities, 'getData');
            spyOn($mdDialog, 'hide');
            spyOn($rootScope, 'notify');

            utilities.sendRequest = function (parameters) {
                if (success) {
                    parameters.callback.onSuccess({
                        status: 200
                    });
                } else {
                    parameters.callback.onError({
                        data: errorResponse
                    });
                }
            };
        });

        it('valid `edit terms and conditions` form & successfull edit', function () {
            var editTermsAndConditionsForm = true;
            success = true;
            vm.page.terms_and_conditions = "terms and conditions";
            vm.editTermsAndConditions(editTermsAndConditionsForm);
            expect(utilities.getData).toHaveBeenCalledWith("challengeCreator");
            expect($mdDialog.hide).toHaveBeenCalled();
            expect($rootScope.notify).toHaveBeenCalledWith("success", "The terms and conditions are successfully updated!");
        });

        it('valid `edit terms and conditions` form & backend error', function () {
            var editTermsAndConditionsForm = true;
            success = false;
            vm.tempTermsAndConditions = "temp terms and conditions";
            vm.page.terms_and_conditions = "terms and conditions";
            vm.editTermsAndConditions(editTermsAndConditionsForm);
            expect(utilities.getData).toHaveBeenCalledWith("challengeCreator");
            expect($mdDialog.hide).toHaveBeenCalled();
            expect(vm.page.terms_and_conditions).toEqual(vm.tempTermsAndConditions);
            expect($rootScope.notify).toHaveBeenCalledWith("error", errorResponse);
        });

        it('invalid `edit terms and conditions` form', function () {
            var editTermsAndConditionsForm = false;
            vm.tempTermsAndConditions = "temp evaluation details";
            vm.page.terms_and_conditions = "terms and conditions";
            vm.editTermsAndConditions(editTermsAndConditionsForm);
            expect(vm.page.terms_and_conditions).toEqual(vm.tempTermsAndConditions);
            expect($mdDialog.hide).toHaveBeenCalled();
        });
    });

    describe('Unit tests for challengeTitleDialog function', function () {
        it('open dialog to `edit challenge title`', function () {
            var $mdDialog = $injector.get('$mdDialog');
            var $mdDialogOpened = false;
            $mdDialog.show = jasmine.createSpy().and.callFake(function () {
                $mdDialogOpened = true;
            });

            vm.page.title = "challenge title";
            vm.challengeTitleDialog();
            expect(vm.tempChallengeTitle).toEqual(vm.page.title);
            expect($mdDialog.show).toHaveBeenCalled();
            expect($mdDialogOpened).toEqual(true);
        });
    });

    describe('Unit tests for editChallengeTitle function \
        `challenges/challenge_host_team/<challenge_host_id>/challenge/<challenge_id>`', function () {
        var success;
        var errorResponse = 'error';

        beforeEach(function () {
            spyOn(utilities, 'getData');
            spyOn($mdDialog, 'hide');
            spyOn($rootScope, 'notify');

            utilities.sendRequest = function (parameters) {
                if (success) {
                    parameters.callback.onSuccess({
                        status: 200
                    });
                } else {
                    parameters.callback.onError({
                        data: errorResponse
                    });
                }
            };
        });

        it('valid `edit terms and conditions` form & successfull edit', function () {
            var editChallengeTitleForm = true;
            success = true;
            vm.page.title = "challenge title";
            vm.editChallengeTitle(editChallengeTitleForm);
            expect(utilities.getData).toHaveBeenCalledWith("challengeCreator");
            expect($mdDialog.hide).toHaveBeenCalled();
            expect($rootScope.notify).toHaveBeenCalledWith("success", "The challenge title is  successfully updated!");
        });

        it('valid `edit terms and conditions` form & backend error', function () {
            var editChallengeTitleForm = true;
            success = false;
            vm.tempChallengeTitle = "temp challenge title";
            vm.page.title = "challenge title";
            vm.editChallengeTitle(editChallengeTitleForm);
            expect(utilities.getData).toHaveBeenCalledWith("challengeCreator");
            expect($mdDialog.hide).toHaveBeenCalled();
            expect(vm.page.title).toEqual(vm.tempChallengeTitle);
            expect($rootScope.notify).toHaveBeenCalledWith("error", errorResponse);
        });

        it('invalid `edit terms and conditions` form', function () {
            var editChallengeTitleForm = false;
            vm.tempChallengeTitle = "temp challenge title";
            vm.page.title = "challenge title";
            vm.editChallengeTitle(editChallengeTitleForm);
            expect(vm.page.title).toEqual(vm.tempChallengeTitle);
            expect($mdDialog.hide).toHaveBeenCalled();
        });
    });

    describe('Unit tests for challengePhaseDialog function', function () {
        it('open dialog to `edit challenge phase`', function () {
            var $mdDialog = $injector.get('$mdDialog');
            var $mdDialogOpened = false;
            $mdDialog.show = jasmine.createSpy().and.callFake(function () {
                $mdDialogOpened = true;
            });

            var phase = {
                start_date: new Date('Fri June 12 2018 22:41:51 GMT+0530'),
                end_date: new Date('Fri June 12 2099 22:41:51 GMT+0530'),
                max_submissions_per_day: 1500
            };
            var ev = new Event('click');
            vm.challengePhaseDialog(ev, phase);
            expect(vm.page.challenge_phase).toEqual(phase);
            expect(vm.page.max_submissions_per_day).toEqual(phase.max_submissions_per_day);
            expect(vm.phaseStartDate).toEqual(moment(phase.start_date));
            expect(vm.phaseEndDate).toEqual(moment(phase.end_date));
            expect(vm.testAnnotationFile).toEqual(null);
            expect(vm.sanityCheckPass).toEqual(true);
            expect(vm.sanityCheck).toEqual("");
            expect($mdDialog.show).toHaveBeenCalled();
            expect($mdDialogOpened).toEqual(true);
        });
    });

    describe('Unit tests for editChallengePhase function \
        `challenges/challenge/<challenge_id>/challenge_phase/<challenge_phase_id>`', function () {
        var success;
        var errorResponse = {
            detail: 'error'
        }

        beforeEach(function () {
            spyOn(utilities, 'getData');
            spyOn(utilities, 'hideLoader');
            spyOn(utilities, 'showLoader');
            spyOn(utilities, 'storeData');
            spyOn($mdDialog, 'hide');
            spyOn($rootScope, 'notify');
            spyOn($state, 'go');

            utilities.sendRequest = function (parameters) {
                if (success) {
                    parameters.callback.onSuccess({
                        data: 'success',
                        status: 200
                    });
                } else {
                    parameters.callback.onError({
                        data: errorResponse
                    });
                }
            };
        });

        it('valid `edit challenge phase` form & successfull edit', function () {
            var editChallengePhaseForm = true;
            success = true;
            vm.page.challenge_phase ={
                id: 1,
                name: "challenge phase name",
                description: "challenge phase description",
                max_submissions_per_day: 500,
                max_submissions: 5000
            };
            vm.phaseStartDate = new Date('Fri June 12 2018 22:41:51 GMT+0530');
            vm.phaseEndDate = new Date('Fri June 12 2099 22:41:51 GMT+0530');

            vm.editChallengePhase(editChallengePhaseForm);
            expect(vm.challengePhaseId).toEqual(vm.page.challenge_phase.id);
            expect(utilities.hideLoader).toHaveBeenCalled();
            expect($mdDialog.hide).toHaveBeenCalled();
            expect($rootScope.notify).toHaveBeenCalledWith("success", "The challenge phase details are successfully updated!");
            expect(utilities.showLoader).toHaveBeenCalled();
        });

        it('valid `edit challenge phase` form & backend error', function () {
            var editChallengePhaseForm = true;
            success = false;
            vm.page.challenge_phase ={
                id: 1,
                name: "challenge phase name",
                description: "challenge phase description",
                max_submissions_per_day: 500,
                max_submissions: 5000
            };
            vm.phaseStartDate = new Date('Fri June 12 2018 22:41:51 GMT+0530');
            vm.phaseEndDate = new Date('Fri June 12 2099 22:41:51 GMT+0530');

            vm.editChallengePhase(editChallengePhaseForm);
            expect(vm.challengePhaseId).toEqual(vm.page.challenge_phase.id);
            expect(utilities.hideLoader).toHaveBeenCalled();
            expect($mdDialog.hide).toHaveBeenCalled();
            expect($rootScope.notify).toHaveBeenCalledWith("error", errorResponse);
            expect(utilities.showLoader).toHaveBeenCalled();
        });

        it('invalid `edit challenge phase` form & get successfully challenge phase details', function () {
            var editChallengePhaseForm = false;
            success = true;
            vm.editChallengePhase(editChallengePhaseForm);
            expect(vm.phases).toEqual('success');
            expect(utilities.hideLoader).toHaveBeenCalled();
            expect($mdDialog.hide).toHaveBeenCalled();
        });

        it('invalid `edit challenge phase` form & backend error', function () {
            var editChallengePhaseForm = false;
            success = false;
            vm.editChallengePhase(editChallengePhaseForm);
            expect(utilities.storeData).toHaveBeenCalledWith('emailError', errorResponse.detail);
            expect($state.go).toHaveBeenCalledWith('web.permission-denied');
            expect(utilities.hideLoader).toHaveBeenCalled();
            expect($mdDialog.hide).toHaveBeenCalled();
        });
    });

    describe('Unit tests for publishChallenge function', function () {
        var ev;

        beforeEach(function () {
            spyOn($mdDialog, 'hide');
            spyOn($state, 'go');

            ev = new Event('click');
            spyOn(ev, 'stopPropagation');
        });

        it('change challenge state from `public` to `private`', function () {
            vm.isPublished = true; 
            vm.publishChallenge(ev);
            expect(vm.publishDesc).toEqual(null);
            expect(ev.stopPropagation).toHaveBeenCalled();
            expect(vm.toggleChallengeState).toEqual('private');
        });

        it('change challenge state from `private` to `public`', function () {
            vm.isPublished = false; 
            vm.publishChallenge(ev);
            expect(vm.publishDesc).toEqual(null);
            expect(ev.stopPropagation).toHaveBeenCalled();
            expect(vm.toggleChallengeState).toEqual('public');
        });

        it('open dialog for confirmation', function () {
            spyOn($mdDialog, 'show').and.callFake(function () {
                var deferred = $injector.get('$q').defer();
                return deferred.promise;
            });
            vm.publishChallenge(ev);
            expect(ev.stopPropagation).toHaveBeenCalled();
            expect($mdDialog.show).toHaveBeenCalled();
        });
    });

    describe('Unit tests for showConfirmation function', function () {
        it('show confirmation message', function () {
            spyOn($rootScope, 'notify');
            var message = "confirmation message";
            vm.showConfirmation(message);
            expect($rootScope.notify).toHaveBeenCalledWith("success", message);
        });
    });

    describe('Unit tests for termsAndConditionDialog function', function () {
        it('open dialog of `terms and conditions`', function () {
            var $mdDialog = $injector.get('$mdDialog');
            var $mdDialogOpened = false;
            $mdDialog.show = jasmine.createSpy().and.callFake(function () {
                $mdDialogOpened = true;
            });

            vm.termsAndConditionDialog();
            expect($mdDialog.show).toHaveBeenCalled();
            expect($mdDialogOpened).toBe(true);
        });
    });
});
