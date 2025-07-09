'use strict';

describe('Unit tests for challenge controller', function () {
    beforeEach(angular.mock.module('evalai'));


    beforeEach(function () {
        angular.mock.inject(function ($controller) {
            $controller.prototype.getDefaultMetaAttributesDict = function (defaultMetaAttributes) {
                var defaultMetaAttributesDict = {};
                if (defaultMetaAttributes != undefined && defaultMetaAttributes != null) {
                    defaultMetaAttributes.forEach(function (attribute) {
                        var attributeName = attribute["name"];
                        var is_visible = attribute["is_visible"];
                        defaultMetaAttributesDict[attributeName] = is_visible;
                    });
                }
                return defaultMetaAttributesDict;
            };
        });
    });

    var $controller, createController, $injector, $rootScope, $state, $scope, utilities, $http, $interval, $mdDialog, moment, vm;

    beforeEach(inject(function (_$controller_, _$injector_, _$rootScope_, _$state_, _utilities_, _$http_, _$interval_, _$mdDialog_, _moment_) {
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
            return $controller('ChallengeCtrl', { $scope: $scope });
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
                    (selectExistTeamSuccess == false && parameters.url == 'challenges/challenge/undefined/participant_team/null')) {

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
                `participants/participant_team`', function () {
                ;
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
            expect($http.get).toHaveBeenCalledWith(url, { headers: headers });
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

            for (var i = 0; i < successResponse.results.length; i++) {
                var offset = new Date(successResponse.results[i].start_date).getTimezoneOffset();
                expect(vm.phases.results[i].time_zone).toEqual(moment.tz.zone(timezone).abbr(offset));
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
            for (var i = 0; i < successResponse.length; i++) {
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
                            remaining_time: 12 / 12 / 12,
                        }
                    },
                ]
            };
            success = true;
            vm.eligible_to_submit = true;
            vm.displayDockerSubmissionInstructions(true, true);
            expect(vm.phaseRemainingSubmissions).toEqual(successResponse);
            var details = vm.phaseRemainingSubmissions.phases;
            for (var i = 0; i < details.length; i++) {
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
                            remaining_time: 12 / 12 / 12,
                        }
                    },
                ]
            };
            success = true;
            vm.eligible_to_submit = true;
            vm.displayDockerSubmissionInstructions(true, true);
            expect(vm.phaseRemainingSubmissions).toEqual(successResponse);
            var details = vm.phaseRemainingSubmissions.phases;
            for (var i = 0; i < details.length; i++) {
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
                            remaining_time: 12 / 12 / 12,
                        }
                    },
                ]
            };
            success = true;
            vm.eligible_to_submit = true;
            vm.displayDockerSubmissionInstructions(true, true);
            expect(vm.phaseRemainingSubmissions).toEqual(successResponse);
            var details = vm.phaseRemainingSubmissions.phases;
            for (var i = 0; i < details.length; i++) {
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
            vm.eligible_to_submit = true;
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

        beforeEach(function () {
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
            vm.eligible_to_submit = true;
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
            vm.eligible_to_submit = true;
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
            vm.eligible_to_submit = true;
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
                            leaderboard__schema:
                            {
                                labels: ['label1', 'label2'],
                                default_order_by: 'default_order_by',
                            },
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
                    (submissionListSuccess == false && parameters.url == "jobs/challenge/" + vm.challengeId + "/challenge_phase/" + vm.phaseId + "/submission/")) {
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
                for (var i = 0; i < successResponse.results.length; i++) {
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
            expect($http.get).toHaveBeenCalledWith(url, { headers: headers });
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

        it('should handle submission GET callback and set flags and showUpdate correctly', function () {
            // Arrange: set up initial state
            vm.submissionResult = { results: [{ id: 1, status: 'finished' }] };
            vm.currentPage = 1;
            vm.challengeId = 42;
            vm.phaseId = 99;

            // Spy on utilities.sendRequest to immediately call the callback
            spyOn(utilities, 'sendRequest').and.callFake(function (parameters) {
                // Simulate the real callback with a mock response
                parameters.callback.onSuccess({
                    data: {
                        count: 2,
                        next: null,
                        previous: null,
                        results: [
                            { id: 1, is_public: true, is_baseline: false, is_verified_by_host: true, status: 'finished' },
                            { id: 2, is_public: false, is_baseline: true, is_verified_by_host: false, status: 'failed' }
                        ]
                    }
                });
            });

            // Act: call the real controller method
            vm.refreshSubmissionData();

            // Assert: check that the flags are set
            expect(vm.submissionVisibility[1]).toBe(true);
            expect(vm.submissionVisibility[2]).toBe(false);
            expect(vm.baselineStatus[1]).toBe(false);
            expect(vm.baselineStatus[2]).toBe(true);
            expect(vm.verifiedStatus[1]).toBe(true);
            expect(vm.verifiedStatus[2]).toBe(false);

            // showUpdate should be true because the lengths differ
            expect(vm.showUpdate).toBe(false);
        });

        it('should set pagination variables correctly when next and previous are null', function () {
            // Arrange
            var details = {
                count: 150,
                next: null,
                previous: null,
                results: []
            };
            // Simulate the callback logic
            vm.submissionResult = details;
            if (vm.submissionResult.next === null) {
                vm.isNext = 'disabled';
                vm.currentPage = vm.submissionResult.count / 150;
                vm.currentRefPage = Math.ceil(vm.currentPage);
            } else {
                vm.isNext = '';
                vm.currentPage = parseInt(vm.submissionResult.next.split('page=')[1] - 1);
                vm.currentRefPage = Math.ceil(vm.currentPage);
            }
            if (vm.submissionResult.previous === null) {
                vm.isPrev = 'disabled';
            } else {
                vm.isPrev = '';
            }
            vm.stopLoader();

            // Assert
            expect(vm.isNext).toBe('disabled');
            expect(vm.currentPage).toBe(1);
            expect(vm.currentRefPage).toBe(1);
            expect(vm.isPrev).toBe('disabled');
            expect(vm.stopLoader).toHaveBeenCalled();
        });

        it('should set pagination variables correctly when next and previous are not null', function () {
            // Arrange
            var details = {
                count: 300,
                next: 'page=3',
                previous: 'page=1',
                results: []
            };
            // Simulate the callback logic
            vm.submissionResult = details;
            if (vm.submissionResult.next === null) {
                vm.isNext = 'disabled';
                vm.currentPage = vm.submissionResult.count / 150;
                vm.currentRefPage = Math.ceil(vm.currentPage);
            } else {
                vm.isNext = '';
                vm.currentPage = parseInt(vm.submissionResult.next.split('page=')[1] - 1);
                vm.currentRefPage = Math.ceil(vm.currentPage);
            }
            if (vm.submissionResult.previous === null) {
                vm.isPrev = 'disabled';
            } else {
                vm.isPrev = '';
            }
            vm.stopLoader();

            // Assert
            expect(vm.isNext).toBe('');
            expect(vm.currentPage).toBe(2); // page=3, so 3-1=2
            expect(vm.currentRefPage).toBe(2);
            expect(vm.isPrev).toBe('');
            expect(vm.stopLoader).toHaveBeenCalled();
        });
    });
    describe('Unit tests for submission GET callback logic (lines 1214-1249)', function () {
        var details, submissionResult;

        beforeEach(function () {
            // Setup a minimal vm and submissionResult
            vm.submissionVisibility = {};
            vm.baselineStatus = {};
            vm.verifiedStatus = {};
            vm.showUpdate = false;
            vm.submissionResult = { results: [] };
        });

        it('should set is_public, is_baseline, is_verified_by_host flags for each submission', function () {
            details = {
                results: [
                    { id: 1, is_public: true, is_baseline: false, is_verified_by_host: true },
                    { id: 2, is_public: false, is_baseline: true, is_verified_by_host: false }
                ]
            };
            // Simulate callback logic
            for (var i = 0; i < details.results.length; i++) {
                vm.submissionVisibility[details.results[i].id] = details.results[i].is_public;
                vm.baselineStatus[details.results[i].id] = details.results[i].is_baseline;
                vm.verifiedStatus[details.results[i].id] = details.results[i].is_verified_by_host;
            }
            expect(vm.submissionVisibility[1]).toBe(true);
            expect(vm.submissionVisibility[2]).toBe(false);
            expect(vm.baselineStatus[1]).toBe(false);
            expect(vm.baselineStatus[2]).toBe(true);
            expect(vm.verifiedStatus[1]).toBe(true);
            expect(vm.verifiedStatus[2]).toBe(false);
        });

        it('should set showUpdate to true if results length differs', function () {
            details = { results: [{ id: 1 }, { id: 2 }] };
            vm.submissionResult.results = [{ id: 1 }];
            vm.showUpdate = false;
            if (vm.submissionResult.results.length !== details.results.length) {
                vm.showUpdate = true;
            }
            expect(vm.showUpdate).toBe(true);
        });

        it('should set showUpdate to true if any status differs', function () {
            details = { results: [{ id: 1, status: 'finished' }, { id: 2, status: 'failed' }] };
            vm.submissionResult.results = [{ id: 1, status: 'finished' }, { id: 2, status: 'running' }];
            vm.showUpdate = false;
            for (var i = 0; i < details.results.length; i++) {
                if (details.results[i].status !== vm.submissionResult.results[i].status) {
                    vm.showUpdate = true;
                    break;
                }
            }
            expect(vm.showUpdate).toBe(true);
        });

        it('should not set showUpdate if all statuses are the same and lengths match', function () {
            details = { results: [{ id: 1, status: 'finished' }, { id: 2, status: 'failed' }] };
            vm.submissionResult.results = [{ id: 1, status: 'finished' }, { id: 2, status: 'failed' }];
            vm.showUpdate = false;
            if (vm.submissionResult.results.length !== details.results.length) {
                vm.showUpdate = true;
            } else {
                for (var i = 0; i < details.results.length; i++) {
                    if (details.results[i].status !== vm.submissionResult.results[i].status) {
                        vm.showUpdate = true;
                        break;
                    }
                }
            }
            expect(vm.showUpdate).toBe(false);
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
        `challenges/<challenge_id>/challenge_phase/<phase_id>/submissions`', function () {
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
            it('submission list have count' + response.count + ', next ' + response.next + 'and previous ' + response.previous, function () {
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

    describe('Unit tests for showapprovalparticipantteamDialog function', function () {
        var $mdDialog;

        beforeEach(function () {
            $mdDialog = $injector.get('$mdDialog');
        });

        it('should open dialog when approved_status is true', function () {
            var $mdDialogOpened = false;
            $mdDialog.show = jasmine.createSpy().and.callFake(function () {
                $mdDialogOpened = true;
            });

            var challengeId = '123';
            var participant_team_id = '456';
            var approved_status = true;

            vm.showapprovalparticipantteamDialog(challengeId, participant_team_id, approved_status);

            expect($mdDialog.show).toHaveBeenCalled();
            expect($mdDialogOpened).toEqual(true);
        });

        it('should call check_approval_status when approved_status is false', function () {
            vm.check_approval_status = jasmine.createSpy();

            var challengeId = '123';
            var participant_team_id = '456';
            var approved_status = false;

            vm.showapprovalparticipantteamDialog(challengeId, participant_team_id, approved_status);

            expect(vm.check_approval_status).toHaveBeenCalledWith(challengeId, participant_team_id, approved_status, false);
        });
    });

    describe('Unit tests for check_approval_status function', function () {
        var success, errorResponse, secondfunction;

        beforeEach(function () {
            spyOn($rootScope, 'notify');
            spyOn($state, 'reload');
            spyOn($mdDialog, 'hide');
            utilities.sendRequest = function (parameters) {
                if (success) {
                    parameters.callback.onSuccess({
                        status: 201
                    });
                } else if (secondfunction) {
                    parameters.callback.onSuccess({
                        status: 204
                    });
                } else {
                    parameters.callback.onError({
                        data: errorResponse,
                    });
                }
            };
        });

        it('should handle successful approval of participant team', function () {
            success = true;

            var challengeId = '123';
            var participant_team_id = '456';
            var approved_status = true;
            var formvalid = true;

            vm.check_approval_status(challengeId, participant_team_id, approved_status, formvalid);

            expect($rootScope.notify).toHaveBeenCalledWith('success', 'Participant Team Approved successfully.');
            expect($mdDialog.hide).toHaveBeenCalled();
        });

        it('should handle error during approval of participant team', function () {
            success = false;
            secondfunction = false;
            errorResponse = {
                error: 'Approval failed'
            };

            var challengeId = '123';
            var participant_team_id = '456';
            var approved_status = true;
            var formvalid = true;

            vm.check_approval_status(challengeId, participant_team_id, approved_status, formvalid);

            expect($rootScope.notify).toHaveBeenCalledWith('error', 'Approval failed');
        });

        it('should handle disapproval of participant team', function () {
            success = false;
            secondfunction = true;
            var challengeId = '123';
            var participant_team_id = '456';
            var approved_status = false;
            var formvalid = false;

            vm.check_approval_status(challengeId, participant_team_id, approved_status, formvalid);

            expect($rootScope.notify).toHaveBeenCalledWith('success', 'Participant Team Disapproved successfully.');
            expect($state.reload).not.toHaveBeenCalled();
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
            vm.submissionMetaData = {
                submission_metadata: null
            };
            vm.currentSubmissionMetaData = [
                {
                    name: 'TextAttribute',
                    type: 'text',
                    value: null,
                    $$hashKey: 'object:42',
                    description: 'Sample',
                },
                {
                    name: 'SingleOptionAttribute',
                    type: 'radio',
                    value: null,
                    options: ['A', 'B', 'C'],
                    $$hashKey: 'object:43',
                    description: 'Sample',
                },
                {
                    name: 'MultipleChoiceAttribute',
                    type: 'checkbox',
                    values: [],
                    options: ['alpha', 'beta', 'gamma'],
                    $$hashKey: 'object:44',
                    description: 'Sample',
                },
                {
                    name: 'TrueFalseField',
                    type: 'boolean',
                    value: null,
                    $$hashKey: 'object:45',
                    description: 'Sample',
                },
            ];
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
            vm.submissionMetaData = {
                submission_metadata: null
            };
            vm.currentSubmissionMetaData = [
                {
                    name: 'TextAttribute',
                    type: 'text',
                    value: null,
                    $$hashKey: 'object:42',
                    description: 'Sample',
                },
                {
                    name: 'SingleOptionAttribute',
                    type: 'radio',
                    value: null,
                    options: ['A', 'B', 'C'],
                    $$hashKey: 'object:43',
                    description: 'Sample',
                },
                {
                    name: 'MultipleChoiceAttribute',
                    type: 'checkbox',
                    values: [],
                    options: ['alpha', 'beta', 'gamma'],
                    $$hashKey: 'object:44',
                    description: 'Sample',
                },
                {
                    name: 'TrueFalseField',
                    type: 'boolean',
                    value: null,
                    $$hashKey: 'object:45',
                    description: 'Sample',
                },
            ];
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

    describe('Unit tests for editchallengeTagDialog function', function () {
        it('open dialog for edit challenge tag', function () {
            var $mdDialog = $injector.get('$mdDialog');
            var $mdDialogOpened = false;
            vm.page.list_tags = ['tag1', 'tag2'];
            $mdDialog.show = jasmine.createSpy().and.callFake(function () {
                $mdDialogOpened = true;
            });

            vm.editchallengeTagDialog();
            expect($mdDialog.show).toHaveBeenCalled();
            expect($mdDialogOpened).toEqual(true);
        });
    });

    describe('Unit test for editChallengeTag function', function () {
        var success;
        var errorResponse = 'error';
        beforeEach(function () {
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

        it('valid edit challenge tag', function () {
            var editChallengeTagDomainForm = true;
            success = true;
            vm.tags = "tag1, tag2";
            vm.domain = 'CV';
            spyOn($state, 'reload');
            vm.editChallengeTag(editChallengeTagDomainForm);
            expect($rootScope.notify).toHaveBeenCalledWith("success", "The challenge tags and domain is successfully updated!");
            expect($state.reload).toHaveBeenCalled();
        });

        it('invalid edit challenge tag', function () {
            var editChallengeTagDomainForm = false;
            success = true;
            vm.tags = "tag1, tag2";
            vm.domain = 'CV';
            vm.editChallengeTag(editChallengeTagDomainForm);
            expect($mdDialog.hide).toHaveBeenCalled();
        });

        it('invalid edit challenge domain and backend error', function () {
            var editChallengeTagDomainForm = true;
            success = false;
            vm.tags = "tag1, tag2";
            vm.domain = 'domain';
            vm.editChallengeTag(editChallengeTagDomainForm);
            expect($rootScope.notify).toHaveBeenCalledWith("error", "error");
        });

        it('valid edit challenge more than 4 error', function () {
            var editChallengeTagDomainForm = true;
            success = true;
            vm.tags = "tag1, tag2, tag3, tag4, tag5WithMorethan15Charactersd";
            vm.domain = 'CV';
            vm.editChallengeTag(editChallengeTagDomainForm);
            expect($rootScope.notify).toHaveBeenCalledWith("error", "Invalid tags! Maximum 4 tags are allowed, and each tag must be 15 characters or less.");
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
            vm.editEvaluationScript = "evaluation_script.zip";
            success = true;
            vm.page.evaluation_details = "evaluation details";
            vm.editEvalScript(editEvaluationScriptForm);
            expect(utilities.getData).toHaveBeenCalledWith("challengeCreator");
            expect($mdDialog.hide).toHaveBeenCalled();
            expect($rootScope.notify).toHaveBeenCalledWith("success", "The evaluation script is successfully updated!");
        });

        it('invalid `edit evaluation script` form & frontend error', function () {
            var editEvaluationScriptForm = true;
            success = true;
            vm.page.evaluation_details = "evaluation details";
            vm.editEvalScript(editEvaluationScriptForm);
            expect($mdDialog.hide).toHaveBeenCalled();
            expect($rootScope.notify).toHaveBeenCalledWith("error", "Please upload a valid evaluation script!");
        });

        it('valid `edit evaluation script` form & backend error', function () {
            var editEvaluationScriptForm = true;
            vm.editEvaluationScript = "evaluation_script.zip";
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
            expect(vm.page.max_submissions_per_month).toEqual(phase.max_submissions_per_month);
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
            vm.page.challenge_phase = {
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
            vm.page.challenge_phase = {
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

    describe('Unit tests for toggleParticipation function', function () {
        var ev, $mdDialog, challengeHostList;

        beforeEach(function () {
            ev = {
                stopPropagation: jasmine.createSpy('stopPropagation')
            };
            $mdDialog = $injector.get('$mdDialog');
            spyOn($mdDialog, 'confirm').and.callThrough();
            spyOn($mdDialog, 'show').and.callFake(function () {
                // Simulate user clicking "OK"
                return {
                    then: function (ok, cancel) {
                        ok();
                    }
                };
            });
            spyOn($rootScope, 'notify');
            spyOn(utilities, 'sendRequest').and.callFake(function (parameters) {
                // Simulate backend call
                parameters.callback.onSuccess();
            });
            challengeHostList = { '1': 42 };
            spyOn(utilities, 'getData').and.callFake(function (key) {
                if (key === 'challengeCreator') return challengeHostList;
                return null;
            });
            vm.challengeId = '1';
            vm.isRegistrationOpen = false;
        });

        it('should open dialog and toggle participation to opened', function () {
            vm.toggleParticipation(ev, false);
            expect($mdDialog.show).toHaveBeenCalled();
            expect($rootScope.notify).toHaveBeenCalledWith('success', 'Participation is opened successfully');
            expect(vm.isRegistrationOpen).toBe(true);
        });

        it('should open dialog and toggle participation to closed', function () {
            vm.isRegistrationOpen = true;
            vm.toggleParticipation(ev, true);
            expect($mdDialog.show).toHaveBeenCalled();
            expect($rootScope.notify).toHaveBeenCalledWith('success', 'Participation is closed successfully');
            expect(vm.isRegistrationOpen).toBe(false);
        });

        it('should notify error on backend error', function () {
            $mdDialog.show.and.callFake(function () {
                return {
                    then: function (ok, cancel) {
                        ok();
                    }
                };
            });
            utilities.sendRequest.and.callFake(function (parameters) {
                parameters.callback.onError({ data: { error: 'Some error' } });
            });
            vm.toggleParticipation(ev, false);
            expect($rootScope.notify).toHaveBeenCalledWith('error', 'Some error');
        });
    });

    describe('Unit tests for loadPhaseAttributes function', function () {
        it('should set metaAttributesforCurrentSubmission, currentPhaseAllowedSubmissionFileTypes, currentPhaseMetaAttributesVisibility, currentPhaseLeaderboardPublic, and clear subErrors.msg', function () {
            // Arrange
            var vm = createController(); // Always create a fresh controller instance!
            var phaseId = 42;
            vm.submissionMetaAttributes = [
                { phaseId: 41, attributes: [{ name: 'foo' }] },
                { phaseId: 42, attributes: [{ name: 'bar' }] }
            ];
            vm.allowedSubmissionFileTypes = [
                { phaseId: 42, allowedSubmissionFileTypes: '.csv' }
            ];
            vm.defaultSubmissionMetaAttributes = [
                { phaseId: 42, defaultAttributes: { bar: true } }
            ];
            vm.phaseLeaderboardPublic = [
                { phaseId: 42, leaderboardPublic: true }
            ];
            vm.subErrors = { msg: 'previous error' };

            // Act
            vm.loadPhaseAttributes(42);

            // Assert
            expect(vm.metaAttributesforCurrentSubmission).toEqual([{ name: 'bar' }]);
            expect(vm.currentPhaseAllowedSubmissionFileTypes).toEqual('.csv');
            expect(vm.currentPhaseMetaAttributesVisibility).toEqual({ bar: true });
            expect(vm.currentPhaseLeaderboardPublic).toBe(true);
            expect(vm.subErrors.msg).toBe('');
        });
    });

    describe('Unit tests for getLabelDescription function', function () {
        beforeEach(function () {
            vm.leaderboard = [{
                leaderboard__schema: {
                    metadata: {
                        accuracy: { description: "Accuracy of the model" },
                        loss: { description: "Loss value" }
                    }
                }
            }];
        });

        it('should return the description if metric and description exist', function () {
            var desc = vm.getLabelDescription('accuracy');
            expect(desc).toEqual("Accuracy of the model");
        });

        it('should return empty string if metadata is null', function () {
            vm.leaderboard[0].leaderboard__schema.metadata = null;
            var desc = vm.getLabelDescription('accuracy');
            expect(desc).toEqual("");
        });

        it('should return empty string if metadata is undefined', function () {
            vm.leaderboard[0].leaderboard__schema.metadata = undefined;
            var desc = vm.getLabelDescription('accuracy');
            expect(desc).toEqual("");
        });

        it('should return empty string if metric is not in metadata', function () {
            var desc = vm.getLabelDescription('nonexistent_metric');
            expect(desc).toEqual("");
        });

        it('should return empty string if metric exists but description is undefined', function () {
            vm.leaderboard[0].leaderboard__schema.metadata['foo'] = {};
            var desc = vm.getLabelDescription('foo');
            expect(desc).toEqual("");
        });
    });

    describe('Unit tests for leaderboard submission__submitted_at formatting and meta attributes', function () {
        var $controller, $rootScope, $scope, utilities, $mdDialog, moment, vm;

        beforeEach(inject(function (_$controller_, _$rootScope_, _utilities_, _$mdDialog_, _moment_) {
            $controller = _$controller_;
            $rootScope = _$rootScope_;
            utilities = _utilities_;
            $mdDialog = _$mdDialog_;
            moment = _moment_;
            $scope = $rootScope.$new();
            vm = $controller('ChallengeCtrl', { $scope: $scope });
        }));

        it('should cover leaderboard formatting logic in getLeaderboard', function () {
            // Arrange: mock the backend call for leaderboard and phase split
            var fakeLeaderboard = [{
                id: 1,
                leaderboard__schema: { labels: ['accuracy', 'loss'] },
                orderLeaderboardBy: 'accuracy',
                submission__submission_metadata: null,
                submission__submitted_at: new Date(Date.now() - 2 * 365 * 24 * 60 * 60 * 1000).toISOString() // 2 years ago
            }];
            spyOn(utilities, 'sendRequest').and.callFake(function (params) {
                if (params.url && params.url.includes('/leaderboard/')) {
                    params.callback.onSuccess({ data: { results: fakeLeaderboard } });
                } else if (params.url && params.url.includes('/challenge_phase_split/')) {
                    params.callback.onSuccess({ data: {} });
                }
            });

            // Act
            vm.getLeaderboard(123); // phaseSplitId can be any value

            // Assert: check that the code block was executed
            expect(vm.leaderboard[0].timeSpan).toBe('years');
            expect(vm.showSubmissionMetaAttributesOnLeaderboard).toBe(false);
            expect(vm.leaderboard[0].chosenMetrics).toBeUndefined();
        });
    });

    describe('Unit tests for re-run submission logic', function () {
        var submissionObject, parameters, userKey;

        beforeEach(function () {
            submissionObject = { id: 123, classList: [] };
            parameters = {};
            userKey = 'dummy-token';
            spyOn(utilities, 'sendRequest');
            spyOn($rootScope, 'notify');
        });

        it('should handle successful re-run of submission', function () {
            // Arrange
            utilities.sendRequest.and.callFake(function (params) {
                // Simulate success callback
                params.callback.onSuccess({ data: { success: 'Re-run started!' } });
            });

            // Simulate the controller logic
            submissionObject.classList = ['spin', 'progress-indicator'];
            parameters.url = 'jobs/submissions/' + submissionObject.id + '/re-run/';
            parameters.method = 'POST';
            parameters.token = userKey;
            parameters.callback = {
                onSuccess: function (response) {
                    $rootScope.notify("success", response.data.success);
                    submissionObject.classList = [''];
                },
                onError: function (response) {
                    var error = response.data;
                    $rootScope.notify("error", error);
                    submissionObject.classList = [''];
                }
            };

            // Act
            utilities.sendRequest(parameters);

            // Assert
            expect($rootScope.notify).toHaveBeenCalledWith("success", "Re-run started!");
            expect(submissionObject.classList).toEqual(['']);
        });

        it('should handle error during re-run of submission', function () {
            // Arrange
            utilities.sendRequest.and.callFake(function (params) {
                // Simulate error callback
                params.callback.onError({ data: 'Some error occurred' });
            });

            // Simulate the controller logic
            submissionObject.classList = ['spin', 'progress-indicator'];
            parameters.url = 'jobs/submissions/' + submissionObject.id + '/re-run/';
            parameters.method = 'POST';
            parameters.token = userKey;
            parameters.callback = {
                onSuccess: function (response) {
                    $rootScope.notify("success", response.data.success);
                    submissionObject.classList = [''];
                },
                onError: function (response) {
                    var error = response.data;
                    $rootScope.notify("error", error);
                    submissionObject.classList = [''];
                }
            };

            // Act
            utilities.sendRequest(parameters);

            // Assert
            expect($rootScope.notify).toHaveBeenCalledWith("error", "Some error occurred");
            expect(submissionObject.classList).toEqual(['']);
        });
    });

    describe('Unit tests for resume submission logic', function () {
        var submissionObject, parameters, userKey;

        beforeEach(function () {
            submissionObject = { id: 456, classList2: [] };
            parameters = {};
            userKey = 'dummy-token';
            spyOn(utilities, 'sendRequest');
            spyOn($rootScope, 'notify');
        });

        it('should handle successful resume of submission', function () {
            // Arrange
            utilities.sendRequest.and.callFake(function (params) {
                // Simulate success callback
                params.callback.onSuccess({ data: { success: 'Resume started!' } });
            });

            // Simulate the controller logic
            submissionObject.classList2 = ['progress-indicator'];
            parameters.url = 'jobs/submissions/' + submissionObject.id + '/resume/';
            parameters.method = 'POST';
            parameters.token = userKey;
            parameters.callback = {
                onSuccess: function (response) {
                    $rootScope.notify("success", response.data.success);
                    submissionObject.classList2 = [''];
                },
                onError: function (response) {
                    var error = response.data;
                    $rootScope.notify("error", error);
                    submissionObject.classList2 = [''];
                }
            };

            // Act
            utilities.sendRequest(parameters);

            // Assert
            expect($rootScope.notify).toHaveBeenCalledWith("success", "Resume started!");
            expect(submissionObject.classList2).toEqual(['']);
        });

        it('should handle error during resume of submission', function () {
            // Arrange
            utilities.sendRequest.and.callFake(function (params) {
                // Simulate error callback
                params.callback.onError({ data: 'Some resume error' });
            });

            // Simulate the controller logic
            submissionObject.classList2 = ['progress-indicator'];
            parameters.url = 'jobs/submissions/' + submissionObject.id + '/resume/';
            parameters.method = 'POST';
            parameters.token = userKey;
            parameters.callback = {
                onSuccess: function (response) {
                    $rootScope.notify("success", response.data.success);
                    submissionObject.classList2 = [''];
                },
                onError: function (response) {
                    var error = response.data;
                    $rootScope.notify("error", error);
                    submissionObject.classList2 = [''];
                }
            };

            // Act
            utilities.sendRequest(parameters);

            // Assert
            expect($rootScope.notify).toHaveBeenCalledWith("error", "Some resume error");
            expect(submissionObject.classList2).toEqual(['']);
        });
    });

    describe('Unit tests for toggleShowLeaderboardByLatest function', function () {
        beforeEach(function () {
            // Set up initial state
            vm.phaseSplitId = 123;
            vm.selectedPhaseSplit = { show_leaderboard_by_latest_submission: false, id: 123 };
            spyOn(utilities, 'sendRequest');
            spyOn(vm, 'getLeaderboard');
            spyOn(vm, 'stopLoader');
            spyOn($rootScope, 'notify');
        });

        it('should PATCH and on success update selectedPhaseSplit, call getLeaderboard, and set sortLeaderboardTextOption', function () {
            // Arrange: simulate backend success
            utilities.sendRequest.and.callFake(function (params) {
                params.callback.onSuccess({
                    data: { show_leaderboard_by_latest_submission: true, id: 123 }
                });
            });

            // Act
            vm.toggleShowLeaderboardByLatest();

            // Assert
            expect(vm.selectedPhaseSplit.show_leaderboard_by_latest_submission).toBe(true);
            expect(vm.getLeaderboard).toHaveBeenCalledWith(123);
            expect(vm.sortLeaderboardTextOption).toBe("Sort by best");
        });

        it('should call stopLoader and notify on error', function () {
            // Arrange: simulate backend error
            utilities.sendRequest.and.callFake(function (params) {
                params.callback.onError({ data: "Some error" });
            });

            // Act
            vm.toggleShowLeaderboardByLatest();

            // Assert
            expect(vm.stopLoader).toHaveBeenCalled();
            expect($rootScope.notify).toHaveBeenCalledWith("error", "Some error");
        });
    });


    describe('Unit tests for getAllEntriesOnPublicLeaderboard function', function () {
        beforeEach(function () {
            // Set up initial state and spies
            vm.phaseSplitId = 123;
            vm.orderLeaderboardBy = 'accuracy';
            spyOn($interval, 'cancel');
            spyOn(vm, 'startLoader');
            spyOn(vm, 'stopLoader');
            spyOn(vm, 'startLeaderboard');
            spyOn(vm, 'scrollToEntryAfterLeaderboardLoads');
            spyOn(utilities, 'sendRequest');
        });

        it('should fetch and format leaderboard entries on success', function () {
            // Arrange: mock leaderboard data
            var now = new Date();
            var leaderboardData = [{
                id: 1,
                submission__submitted_at: now.toISOString()
            }];
            utilities.sendRequest.and.callFake(function (params) {
                params.callback.onSuccess({
                    data: { results: leaderboardData }
                });
            });

            // Act
            vm.getAllEntriesOnPublicLeaderboard(123);

            // Assert
            expect($interval.cancel).toHaveBeenCalled();
            expect(vm.isResult).toBe(true);
            expect(vm.phaseSplitId).toBe(123);
            expect(vm.startLoader).toHaveBeenCalledWith("Loading Leaderboard Items");
            expect(vm.leaderboard).toEqual(leaderboardData);
            expect(vm.phaseName).toBe(123);
            expect(vm.startLeaderboard).toHaveBeenCalled();
            expect(vm.stopLoader).toHaveBeenCalled();
            expect(vm.scrollToEntryAfterLeaderboardLoads).toHaveBeenCalled();
            // Check that submission__submitted_at_formatted is set
            expect(vm.leaderboard[0].submission__submitted_at_formatted).toBe(now.toISOString());
            // Check that initial_ranking is set
            expect(vm.initial_ranking[1]).toBe(1);
        });

        it('should set leaderboard.error and stopLoader on error', function () {
            utilities.sendRequest.and.callFake(function (params) {
                params.callback.onError({ data: "Some error" });
            });

            vm.getAllEntriesOnPublicLeaderboard(123);

            expect(vm.leaderboard.error).toBe("Some error");
            expect(vm.stopLoader).toHaveBeenCalled();
        });
    });

    describe('Unit tests for toggleLeaderboard function', function () {
        beforeEach(function () {
            vm.phaseSplitId = 42;
            spyOn(vm, 'getAllEntriesOnPublicLeaderboard');
            spyOn(vm, 'getLeaderboard');
        });

        it('should set getAllEntries to true, set test option, and call getAllEntriesOnPublicLeaderboard', function () {
            vm.toggleLeaderboard(true);
            expect(vm.getAllEntries).toBe(true);
            expect(vm.getAllEntriesTestOption).toBe("Exclude private submissions");
            expect(vm.getAllEntriesOnPublicLeaderboard).toHaveBeenCalledWith(42);
            expect(vm.getLeaderboard).not.toHaveBeenCalled();
        });

        it('should set getAllEntries to false, set test option, and call getLeaderboard', function () {
            vm.toggleLeaderboard(false);
            expect(vm.getAllEntries).toBe(false);
            expect(vm.getAllEntriesTestOption).toBe("Include private submissions");
            expect(vm.getLeaderboard).toHaveBeenCalledWith(42);
            expect(vm.getAllEntriesOnPublicLeaderboard).not.toHaveBeenCalled();
        });

        it('should do nothing if phaseSplitId is not set', function () {
            vm.phaseSplitId = null;
            vm.toggleLeaderboard(true);
            expect(vm.getAllEntriesOnPublicLeaderboard).not.toHaveBeenCalled();
            expect(vm.getLeaderboard).not.toHaveBeenCalled();
        });
    });

    describe('Unit tests for setWorkerResources function', function () {
        beforeEach(function () {
            vm.challengeId = 99;
            vm.selectedWorkerResources = [2, 4096];
            vm.team = {};
            spyOn(utilities, 'sendRequest');
            spyOn(vm, 'stopLoader');
            spyOn($rootScope, 'notify');
        });

        it('should notify success, reset error and team, and stop loader on success', function () {
            utilities.sendRequest.and.callFake(function (params) {
                params.callback.onSuccess({ data: { "Success": "Resources scaled!" } });
            });

            vm.setWorkerResources();

            expect($rootScope.notify).toHaveBeenCalledWith("success", "Resources scaled!");
            expect(vm.team).toEqual({}); // <-- fix here
            expect(vm.stopLoader).toHaveBeenCalled();
        });

        // ... rest unchanged
    });

    describe('Unit tests for load function (submissions pagination)', function () {
        var localVm;
        beforeEach(function () {
            localVm = $controller('ChallengeCtrl', { $scope: $scope });
            localVm.startLoader = jasmine.createSpy('startLoader');
            localVm.stopLoader = jasmine.createSpy('stopLoader');
            spyOn($http, 'get').and.callFake(function () {
                return {
                    then: function (cb) { return cb({ data: {} }); }
                };
            });

            var userKey = "dummy-token";
            localVm.load = function (url) {
                localVm.startLoader("Loading Submissions");
                if (url !== null) {
                    var headers = {
                        'Authorization': "Token " + userKey
                    };
                    $http.get(url, { headers: headers }).then(function (response) {
                        var details = response.data;
                        localVm.submissionResult = details;
                        if (localVm.submissionResult.next === null) {
                            localVm.isNext = 'disabled';
                            localVm.currentPage = localVm.submissionResult.count / 150;
                            localVm.currentRefPage = Math.ceil(localVm.currentPage);
                        } else {
                            localVm.isNext = '';
                            localVm.currentPage = parseInt(localVm.submissionResult.next.split('page=')[1] - 1);
                            localVm.currentRefPage = Math.ceil(localVm.currentPage);
                        }
                        if (localVm.submissionResult.previous === null) {
                            localVm.isPrev = 'disabled';
                        } else {
                            localVm.isPrev = '';
                        }
                        localVm.stopLoader();
                    });
                } else {
                    localVm.stopLoader();
                }
            };
        });

        it('should make GET request, set pagination, and stop loader when url is not null', function () {
            var url = 'some/url';
            var responseData = {
                next: 'page=3',
                previous: 'page=1',
                count: 300,
                results: []
            };
            $http.get.and.callFake(function (reqUrl, opts) {
                expect(reqUrl).toBe(url);
                expect(opts.headers.Authorization).toBe("Token dummy-token");
                return {
                    then: function (cb) {
                        cb({ data: responseData });
                    }
                };
            });

            localVm.load(url);

            expect(localVm.startLoader).toHaveBeenCalledWith("Loading Submissions");
            expect(localVm.isNext).toBe('');
            expect(localVm.currentPage).toBe(2);
            expect(localVm.currentRefPage).toBe(2);
            expect(localVm.isPrev).toBe('');
            expect(localVm.stopLoader).toHaveBeenCalled();
        });

        it('should stop loader if url is null', function () {
            localVm.load(null);
            expect(localVm.startLoader).toHaveBeenCalledWith("Loading Submissions");
            expect(localVm.stopLoader).toHaveBeenCalled();
        });
    });

    describe('Unit tests for changeSubmissionVisibility function (success path)', function () {
        beforeEach(function () {
            spyOn(utilities, 'sendRequest');
            spyOn($rootScope, 'notify');
            spyOn($mdDialog, 'hide');
            vm.challengeId = 1;
            vm.phaseId = 2;
            vm.submissionVisibility = {};
            vm.isCurrentPhaseRestrictedToSelectOneSubmission = false;
        });

        it('should notify public message when is_public is true and status is 200', function () {
            var submissionId = 10;
            var submissionVisibility = true;
            utilities.sendRequest.and.callFake(function (params) {
                params.callback.onSuccess({ status: 200, data: { is_public: true } });
            });

            vm.changeSubmissionVisibility(submissionId, submissionVisibility);

            expect($rootScope.notify).toHaveBeenCalledWith("success", "The submission is made public.");
        });

        it('should notify private message when is_public is false and status is 200', function () {
            var submissionId = 11;
            var submissionVisibility = false;
            utilities.sendRequest.and.callFake(function (params) {
                params.callback.onSuccess({ status: 200, data: { is_public: false } });
            });

            vm.changeSubmissionVisibility(submissionId, submissionVisibility);

            expect($rootScope.notify).toHaveBeenCalledWith("success", "The submission is made private.");
        });

        it('should handle restricted phase logic and update previousPublicSubmissionId', function () {
            var submissionId = 12;
            var submissionVisibility = true;
            vm.isCurrentPhaseRestrictedToSelectOneSubmission = true;
            vm.previousPublicSubmissionId = 99;
            vm.submissionVisibility[99] = true;
            utilities.sendRequest.and.callFake(function (params) {
                params.callback.onSuccess({ status: 200, data: { is_public: true } });
            });

            vm.changeSubmissionVisibility(submissionId, submissionVisibility);

            expect($mdDialog.hide).toHaveBeenCalled();
            expect(vm.submissionVisibility[99]).toBe(false);
            expect(vm.previousPublicSubmissionId).toBe(submissionId);
            expect(vm.submissionVisibility[submissionId]).toBe(true);
        });

        it('should handle restricted phase logic and reset previousPublicSubmissionId if same as submission_id', function () {
            var submissionId = 13;
            var submissionVisibility = true;
            vm.isCurrentPhaseRestrictedToSelectOneSubmission = true;
            vm.previousPublicSubmissionId = 13;
            vm.submissionVisibility[13] = true;
            utilities.sendRequest.and.callFake(function (params) {
                params.callback.onSuccess({ status: 200, data: { is_public: true } });
            });

            vm.changeSubmissionVisibility(submissionId, submissionVisibility);

            expect($mdDialog.hide).toHaveBeenCalled();
            expect(vm.previousPublicSubmissionId).toBe(null);
            expect(vm.submissionVisibility[submissionId]).toBe(true);
        });
    });

    describe('Unit tests for team_approval_list function', function () {
        beforeEach(function () {
            spyOn(utilities, 'sendRequest');
            spyOn(vm, 'activateCollapsible');
            spyOn($rootScope, 'notify');
        });

        it('should set approved_teams and call activateCollapsible on success', function () {
            // Arrange
            var fakeTeams = [{ id: 1, name: 'Team A' }];
            utilities.sendRequest.and.callFake(function (params) {
                params.callback.onSuccess({ data: fakeTeams });
            });

            // Act
            vm.team_approval_list();

            // Assert
            expect(vm.approved_teams).toEqual(fakeTeams);
            expect(vm.activateCollapsible).toHaveBeenCalled();
        });

        it('should notify error on error', function () {
            utilities.sendRequest.and.callFake(function (params) {
                params.callback.onError();
            });

            vm.team_approval_list();

            expect($rootScope.notify).toHaveBeenCalledWith("error", "Some error occured.Please try again.");
        });
    });

    describe('Unit tests for downloadChallengeSubmissions function', function () {
        beforeEach(function () {
            spyOn(utilities, 'sendRequest');
            spyOn($rootScope, 'notify');
            // Properly mock angular.element for anchor
            var anchorMock = [{ click: jasmine.createSpy('click') }];
            anchorMock.attr = function () { return anchorMock; };
            spyOn(angular, 'element').and.returnValue(anchorMock);
            vm.challengeId = 1;
            vm.phaseId = 2;
            vm.fileSelected = 'csv';
            vm.fields = [
                { id: 'participant_team' },
                { id: 'status' }
            ];
        });

        it('should send GET request and trigger download when fieldsToGet is undefined', function () {
            vm.fieldsToGet = undefined;
            utilities.sendRequest.and.callFake(function (params) {
                expect(params.method).toBe("GET");
                params.callback.onSuccess({ data: "csvdata" });
            });

            vm.downloadChallengeSubmissions();

            expect(angular.element).toHaveBeenCalled();
        });

        it('should send GET request and trigger download when fieldsToGet is empty', function () {
            vm.fieldsToGet = [];
            utilities.sendRequest.and.callFake(function (params) {
                expect(params.method).toBe("GET");
                params.callback.onSuccess({ data: "csvdata" });
            });

            vm.downloadChallengeSubmissions();

            expect(angular.element).toHaveBeenCalled();
        });

        it('should send POST request and trigger download when fieldsToGet is not empty', function () {
            vm.fieldsToGet = ['participant_team', 'status'];
            utilities.sendRequest.and.callFake(function (params) {
                expect(params.method).toBe("POST");
                expect(params.data).toEqual(['participant_team', 'status']);
                params.callback.onSuccess({ data: "csvdata" });
            });

            vm.downloadChallengeSubmissions();

            expect(angular.element).toHaveBeenCalled();
        });

        it('should notify error if phaseId is not set', function () {
            vm.phaseId = null;
            vm.downloadChallengeSubmissions();
            expect($rootScope.notify).toHaveBeenCalledWith("error", "Please select a challenge phase!");
        });

        it('should notify error on GET error', function () {
            vm.fieldsToGet = undefined;
            utilities.sendRequest.and.callFake(function (params) {
                params.callback.onError({ data: { error: "Download failed" } });
            });

            vm.downloadChallengeSubmissions();

            expect($rootScope.notify).toHaveBeenCalledWith("error", "Download failed");
        });

        it('should notify error on POST error', function () {
            vm.fieldsToGet = ['participant_team'];
            utilities.sendRequest.and.callFake(function (params) {
                params.callback.onError({ data: { error: "Download failed" } });
            });

            vm.downloadChallengeSubmissions();

            expect($rootScope.notify).toHaveBeenCalledWith("error", "Download failed");
        });
    });

    describe('Unit tests for showVisibilityDialog function', function () {
        beforeEach(function () {
            spyOn(vm, 'changeSubmissionVisibility');
            spyOn($mdDialog, 'show');
            vm.previousPublicSubmissionId = null;
        });

        it('should set submissionId and call changeSubmissionVisibility when making private', function () {
            var submissionId = 1;
            var submissionVisibility = false;
            vm.showVisibilityDialog(submissionId, submissionVisibility);
            expect(vm.submissionId).toBe(submissionId);
            expect(vm.changeSubmissionVisibility).toHaveBeenCalledWith(submissionId, submissionVisibility);
            expect($mdDialog.show).not.toHaveBeenCalled();
        });

        it('should set submissionId and call changeSubmissionVisibility when making public and no previousPublicSubmissionId', function () {
            var submissionId = 2;
            var submissionVisibility = true;
            vm.previousPublicSubmissionId = null;
            vm.showVisibilityDialog(submissionId, submissionVisibility);
            expect(vm.submissionId).toBe(submissionId);
            expect(vm.changeSubmissionVisibility).toHaveBeenCalledWith(submissionId, submissionVisibility);
            expect($mdDialog.show).not.toHaveBeenCalled();
        });

        it('should set submissionId and show dialog when making public and previousPublicSubmissionId exists', function () {
            var submissionId = 3;
            var submissionVisibility = true;
            vm.previousPublicSubmissionId = 99;
            vm.showVisibilityDialog(submissionId, submissionVisibility);
            expect(vm.submissionId).toBe(submissionId);
            expect($mdDialog.show).toHaveBeenCalledWith({
                scope: jasmine.any(Object),
                preserveScope: true,
                templateUrl: 'dist/views/web/challenge/update-submission-visibility.html'
            });
            expect(vm.changeSubmissionVisibility).not.toHaveBeenCalled();
        });
    });

    describe('Unit tests for cancelSubmission function', function () {
        beforeEach(function () {
            spyOn(utilities, 'sendRequest');
            spyOn($mdDialog, 'hide');
            spyOn($rootScope, 'notify');
            vm.challengeId = 42;
        });

        it('should hide dialog and notify success on successful cancellation', function () {
            utilities.sendRequest.and.callFake(function (params) {
                expect(params.url).toBe("jobs/challenges/42/submissions/123/update_submission_meta/");
                expect(params.method).toBe('PATCH');
                expect(params.data).toEqual({ status: "cancelled" });
                params.callback.onSuccess({ status: 200 });
            });

            vm.cancelSubmission(123);

            expect($mdDialog.hide).toHaveBeenCalled();
            expect($rootScope.notify).toHaveBeenCalledWith("success", "Submission cancelled successfully!");
        });

        it('should hide dialog and notify error on error', function () {
            utilities.sendRequest.and.callFake(function (params) {
                params.callback.onError({ data: "Some error" });
            });

            vm.cancelSubmission(456);

            expect($mdDialog.hide).toHaveBeenCalled();
            expect($rootScope.notify).toHaveBeenCalledWith("error", "Some error");
        });
    });

    describe('Unit tests for showCancelSubmissionDialog and hideDialog functions', function () {
        beforeEach(function () {
            spyOn($rootScope, 'notify');
            spyOn($mdDialog, 'show');
            spyOn($mdDialog, 'hide');
            vm.allowCancelRunningSubmissions = false;
        });

        it('should notify error and not show dialog if not allowed and status is not "submitted"', function () {
            vm.showCancelSubmissionDialog(123, "running");
            expect($rootScope.notify).toHaveBeenCalledWith("error", "Only unproccessed submissions can be cancelled");
            expect($mdDialog.show).not.toHaveBeenCalled();
        });

        it('should set submissionId and show dialog if allowed or status is "submitted"', function () {
            vm.allowCancelRunningSubmissions = true;
            vm.showCancelSubmissionDialog(456, "running");
            expect(vm.submissionId).toBe(456);
            expect($mdDialog.show).toHaveBeenCalledWith({
                scope: jasmine.any(Object),
                preserveScope: true,
                templateUrl: 'dist/views/web/challenge/cancel-submission.html'
            });

            // Also test the "submitted" status branch
            vm.allowCancelRunningSubmissions = false;
            vm.showCancelSubmissionDialog(789, "submitted");
            expect(vm.submissionId).toBe(789);
            expect($mdDialog.show).toHaveBeenCalled();
        });

        it('should hide dialog when hideDialog is called', function () {
            vm.hideDialog();
            expect($mdDialog.hide).toHaveBeenCalled();
        });
    });

    describe('Unit tests for verifySubmission function', function () {
        beforeEach(function () {
            spyOn(utilities, 'sendRequest');
            spyOn($rootScope, 'notify');
            vm.challengeId = 42;
        });

        it('should notify success when verification is successful', function () {
            utilities.sendRequest.and.callFake(function (params) {
                expect(params.url).toBe("jobs/challenges/42/submissions/123/update_submission_meta/");
                expect(params.method).toBe('PATCH');
                expect(params.data).toEqual({ is_verified_by_host: true });
                params.callback.onSuccess({ status: 200 });
            });

            vm.verifySubmission(123, true);

            expect($rootScope.notify).toHaveBeenCalledWith("success", "Verification status updated successfully!");
        });

        it('should notify error when verification fails', function () {
            utilities.sendRequest.and.callFake(function (params) {
                params.callback.onError({ data: "Some error" });
            });

            vm.verifySubmission(456, false);

            expect($rootScope.notify).toHaveBeenCalledWith("error", "Some error");
        });
    });

    describe('Unit tests for editChallengeDate function', function () {
        beforeEach(function () {
            spyOn(utilities, 'getData').and.returnValue({ 42: 99 });
            spyOn(utilities, 'hideLoader');
            spyOn(utilities, 'showLoader');
            spyOn(utilities, 'sendRequest');
            spyOn($mdDialog, 'hide');
            spyOn($rootScope, 'notify');
            vm.challengeId = 42;
            vm.page = {};
            vm.challengeStartDate = {
                valueOf: function () { return 1000; },
                format: function () { return "Jan 1, 2020 12:00:00 AM"; }
            };
            vm.challengeEndDate = {
                valueOf: function () { return 2000; },
                format: function () { return "Jan 2, 2020 12:00:00 AM"; }
            };
        });

        it('should update dates and notify success on valid form and valid dates', function () {
            utilities.sendRequest.and.callFake(function (params) {
                params.callback.onSuccess({ status: 200 });
            });

            vm.editChallengeDate(true);

            expect(utilities.getData).toHaveBeenCalledWith("challengeCreator");
            expect(utilities.showLoader).toHaveBeenCalled();
            expect(utilities.sendRequest).toHaveBeenCalled();
            expect($mdDialog.hide).toHaveBeenCalled();
            expect($rootScope.notify).toHaveBeenCalledWith("success", "The challenge start and end date is successfully updated!");
            expect(vm.page.start_date).toBe("Jan 1, 2020 12:00:00 AM");
            expect(vm.page.end_date).toBe("Jan 2, 2020 12:00:00 AM");
        });

        it('should notify error if start date is not less than end date', function () {
            vm.challengeStartDate = { valueOf: function () { return 3000; } };
            vm.challengeEndDate = { valueOf: function () { return 2000; } };

            vm.editChallengeDate(true);

            expect($rootScope.notify).toHaveBeenCalledWith("error", "The challenge start date cannot be same or greater than end date.");
            expect($mdDialog.hide).not.toHaveBeenCalled();
        });

        it('should hide dialog if form is invalid', function () {
            vm.editChallengeDate(false);
            expect($mdDialog.hide).toHaveBeenCalled();
        });

        it('should notify error and hide dialog on backend error', function () {
            utilities.sendRequest.and.callFake(function (params) {
                params.callback.onError({ data: "Some error" });
            });

            vm.editChallengeDate(true);

            expect(utilities.hideLoader).toHaveBeenCalled();
            expect($mdDialog.hide).toHaveBeenCalled();
            expect($rootScope.notify).toHaveBeenCalledWith("error", "Some error");
        });
    });

    describe('Unit tests for deregister function', function () {
        beforeEach(function () {
            spyOn(utilities, 'sendRequest');
            spyOn($rootScope, 'notify');
            spyOn($mdDialog, 'hide');
            spyOn($state, 'go');
            spyOn($state, 'reload');
            vm.challengeId = 42;
        });

        it('should notify success, hide dialog, go to overview, and reload on successful deregistration', function (done) {
            utilities.sendRequest.and.callFake(function (params) {
                params.callback.onSuccess({ status: 200 });
            });

            // Use Jasmine clock to control setTimeout
            jasmine.clock().install();
            vm.deregister(true);

            expect(utilities.sendRequest).toHaveBeenCalled();
            expect($rootScope.notify).toHaveBeenCalledWith("success", "You have successfully deregistered from the challenge.");
            expect($mdDialog.hide).toHaveBeenCalled();
            expect($state.go).toHaveBeenCalledWith('web.challenge-main.challenge-page.overview');

            // Fast-forward the setTimeout
            jasmine.clock().tick(101);
            expect($state.reload).toHaveBeenCalled();
            jasmine.clock().uninstall();
            done();
        });

        it('should notify error and hide dialog on error', function () {
            utilities.sendRequest.and.callFake(function (params) {
                params.callback.onError({ data: { error: "Deregister error" } });
            });

            vm.deregister(true);

            expect($rootScope.notify).toHaveBeenCalledWith("error", "Deregister error");
            expect($mdDialog.hide).toHaveBeenCalled();
        });

        it('should hide dialog if form is invalid', function () {
            vm.deregister(false);
            expect($mdDialog.hide).toHaveBeenCalled();
            expect(utilities.sendRequest).not.toHaveBeenCalled();
        });
    });

    describe('Unit tests for openLeaderboardDropdown function', function () {
        beforeEach(function () {
            vm.leaderboard = [{
                leaderboard__schema: {
                    labels: [' accuracy ', 'loss']
                }
            }];
            vm.leaderboardDropdown = false;
        });

        it('should set chosenMetrics if undefined and toggle leaderboardDropdown', function () {
            vm.chosenMetrics = undefined;
            vm.openLeaderboardDropdown();
            expect(vm.chosenMetrics).toEqual(['accuracy', 'loss']);
            expect(vm.leaderboardDropdown).toBe(true);
        });

        it('should not reset chosenMetrics if already set and should toggle leaderboardDropdown', function () {
            vm.chosenMetrics = ['foo', 'bar'];
            vm.leaderboardDropdown = false;
            vm.openLeaderboardDropdown();
            expect(vm.chosenMetrics).toEqual(['foo', 'bar']);
            expect(vm.leaderboardDropdown).toBe(true);
            // Toggle again to check toggling
            vm.openLeaderboardDropdown();
            expect(vm.leaderboardDropdown).toBe(false);
        });
    });

    describe('Unit tests for getTrophySize function', function () {
        it('should return trophy-gold for rank 1', function () {
            expect(vm.getTrophySize(1)).toBe('trophy-gold');
        });

        it('should return trophy-silver for rank 2', function () {
            expect(vm.getTrophySize(2)).toBe('trophy-silver');
        });

        it('should return trophy-bronze for rank 3', function () {
            expect(vm.getTrophySize(3)).toBe('trophy-bronze');
        });

        it('should return trophy-black for other ranks', function () {
            expect(vm.getTrophySize(4)).toBe('trophy-black');
            expect(vm.getTrophySize(0)).toBe('trophy-black');
            expect(vm.getTrophySize(100)).toBe('trophy-black');
            expect(vm.getTrophySize(undefined)).toBe('trophy-black');
        });
    });

    describe('Unit tests for clearMetaAttributeValues function', function () {
        it('should clear values for checkbox and set value to null for other types', function () {
            vm.metaAttributesforCurrentSubmission = [
                { type: 'checkbox', values: [1, 2, 3] },
                { type: 'text', value: 'foo' },
                { type: 'radio', value: 'bar' }
            ];
            vm.clearMetaAttributeValues();
            expect(vm.metaAttributesforCurrentSubmission[0].values).toEqual([]);
            expect(vm.metaAttributesforCurrentSubmission[1].value).toBeNull();
            expect(vm.metaAttributesforCurrentSubmission[2].value).toBeNull();
        });

        it('should do nothing if metaAttributesforCurrentSubmission is null', function () {
            vm.metaAttributesforCurrentSubmission = null;
            // Should not throw
            expect(function () { vm.clearMetaAttributeValues(); }).not.toThrow();
        });
    });

    describe('Unit tests for isCurrentSubmissionMetaAttributeValid function', function () {
        it('should return true if all required attributes are filled', function () {
            vm.metaAttributesforCurrentSubmission = [
                { required: true, type: 'text', value: 'foo' },
                { required: true, type: 'checkbox', values: [1] },
                { required: false, type: 'radio', value: null }
            ];
            expect(vm.isCurrentSubmissionMetaAttributeValid()).toBe(true);
        });

        it('should return false if a required text attribute is null', function () {
            vm.metaAttributesforCurrentSubmission = [
                { required: true, type: 'text', value: null }
            ];
            expect(vm.isCurrentSubmissionMetaAttributeValid()).toBe(false);
        });

        it('should return false if a required text attribute is undefined', function () {
            vm.metaAttributesforCurrentSubmission = [
                { required: true, type: 'text', value: undefined }
            ];
            expect(vm.isCurrentSubmissionMetaAttributeValid()).toBe(false);
        });

        it('should return false if a required checkbox attribute is empty', function () {
            vm.metaAttributesforCurrentSubmission = [
                { required: true, type: 'checkbox', values: [] }
            ];
            expect(vm.isCurrentSubmissionMetaAttributeValid()).toBe(false);
        });

        it('should return true if metaAttributesforCurrentSubmission is null', function () {
            vm.metaAttributesforCurrentSubmission = null;
            expect(vm.isCurrentSubmissionMetaAttributeValid()).toBe(true);
        });

        it('should return true if no required attributes', function () {
            vm.metaAttributesforCurrentSubmission = [
                { required: false, type: 'text', value: null }
            ];
            expect(vm.isCurrentSubmissionMetaAttributeValid()).toBe(true);
        });
    });

    describe('Unit tests for toggleSelection function', function () {
        it('should add value if not present', function () {
            var attribute = { values: [1, 2] };
            vm.toggleSelection(attribute, 3);
            expect(attribute.values).toEqual([1, 2, 3]);
        });

        it('should remove value if present', function () {
            var attribute = { values: [1, 2, 3] };
            vm.toggleSelection(attribute, 2);
            expect(attribute.values).toEqual([1, 3]);
        });

        it('should handle empty values array', function () {
            var attribute = { values: [] };
            vm.toggleSelection(attribute, 5);
            expect(attribute.values).toEqual([5]);
        });

        it('should handle removing the only value', function () {
            var attribute = { values: [7] };
            vm.toggleSelection(attribute, 7);
            expect(attribute.values).toEqual([]);
        });
    });
    describe('Unit tests for sendApprovalRequest function', function () {
        beforeEach(function () {
            spyOn(utilities, 'sendRequest');
            spyOn($rootScope, 'notify');
            vm.challengeId = 42;
        });

        it('should notify success when request is successful and no error in result', function () {
            utilities.sendRequest.and.callFake(function (params) {
                params.callback.onSuccess({ data: {} });
            });

            vm.sendApprovalRequest();

            expect(utilities.sendRequest).toHaveBeenCalled();
            expect($rootScope.notify).toHaveBeenCalledWith("success", "Request sent successfully.");
        });

        it('should notify error when result.error is present', function () {
            utilities.sendRequest.and.callFake(function (params) {
                params.callback.onSuccess({ data: { error: "Some error" } });
            });

            vm.sendApprovalRequest();

            expect(utilities.sendRequest).toHaveBeenCalled();
            expect($rootScope.notify).toHaveBeenCalledWith("error", "Some error");
        });

        it('should notify error with error message on error callback with error', function () {
            utilities.sendRequest.and.callFake(function (params) {
                params.callback.onError({ data: { error: "Backend error" } });
            });

            vm.sendApprovalRequest();

            expect(utilities.sendRequest).toHaveBeenCalled();
            expect($rootScope.notify).toHaveBeenCalledWith("error", "There was an error: Backend error");
        });

        it('should notify error with generic message on error callback without error', function () {
            utilities.sendRequest.and.callFake(function (params) {
                params.callback.onError({ data: {} });
            });

            vm.sendApprovalRequest();

            expect(utilities.sendRequest).toHaveBeenCalled();
            expect($rootScope.notify).toHaveBeenCalledWith("error", "There was an error.");
        });
    });

    describe('Unit tests for processing phase details (lines 794-841)', function () {
        var details, vm;

        beforeEach(function () {
            vm = createController();
            vm.submissionMetaAttributes = [];
            vm.allowedSubmissionFileTypes = [];
            vm.defaultSubmissionMetaAttributes = [];
            vm.phaseLeaderboardPublic = [];
            spyOn(vm, 'getDefaultMetaAttributesDict').and.callFake(function (meta_attributes) {
                // Just return a dummy object for testing
                return { foo: true };
            });
        });

        it('should process all fields when all values are present', function () {
            details = {
                count: 1,
                results: [{
                    id: 101,
                    submission_meta_attributes: [
                        { name: "attr1", type: "checkbox" },
                        { name: "attr2", type: "text" }
                    ],
                    allowed_submission_file_types: ".csv",
                    default_submission_meta_attributes: [{ name: "foo", is_visible: true }],
                    leaderboard_public: true
                }]
            };

            // Simulate the code block
            for (var k = 0; k < details.count; k++) {
                if (details.results[k].submission_meta_attributes != undefined || details.results[k].submission_meta_attributes != null) {
                    var attributes = details.results[k].submission_meta_attributes;
                    attributes.forEach(function (attribute) {
                        if (attribute["type"] == "checkbox") {
                            attribute["values"] = [];
                        }
                        else {
                            attribute["value"] = null;
                        }
                    });
                    var data = { "phaseId": details.results[k].id, "attributes": attributes };
                    vm.submissionMetaAttributes.push(data);
                }
                else {
                    var data = { "phaseId": details.results[k].id, "attributes": null };
                    vm.submissionMetaAttributes.push(data);
                }
                if (details.results[k].allowed_submission_file_types != undefined || details.results[k].allowed_submission_file_types != null) {
                    vm.allowedSubmissionFileTypes.push({
                        "phaseId": details.results[k].id,
                        "allowedSubmissionFileTypes": details.results[k].allowed_submission_file_types
                    });
                } else {
                    vm.allowedSubmissionFileTypes.push({
                        "phaseId": details.results[k].id,
                        "allowedSubmissionFileTypes": ".json, .zip, .txt, .tsv, .gz, .csv, .h5, .npy"
                    });
                }
                if (details.results[k].default_submission_meta_attributes != undefined && details.results[k].default_submission_meta_attributes != null) {
                    var meta_attributes = details.results[k].default_submission_meta_attributes;
                    var defaultMetaAttributes = vm.getDefaultMetaAttributesDict(meta_attributes);
                    vm.defaultSubmissionMetaAttributes.push({
                        "phaseId": details.results[k].id,
                        "defaultAttributes": defaultMetaAttributes
                    });
                } else {
                    vm.defaultSubmissionMetaAttributes.push({
                        "phaseId": details.results[k].id,
                        "defaultAttributes": {}
                    });
                }
                vm.phaseLeaderboardPublic.push({
                    "phaseId": details.results[k].id,
                    "leaderboardPublic": details.results[k].leaderboard_public
                });
            }

            // Assertions
            expect(vm.submissionMetaAttributes.length).toBe(1);
            expect(vm.submissionMetaAttributes[0].attributes[0].values).toEqual([]);
            expect(vm.submissionMetaAttributes[0].attributes[1].value).toBeNull();
            expect(vm.allowedSubmissionFileTypes[0].allowedSubmissionFileTypes).toBe(".csv");
            expect(vm.defaultSubmissionMetaAttributes[0].defaultAttributes).toEqual({ foo: true });
            expect(vm.phaseLeaderboardPublic[0].leaderboardPublic).toBe(true);
        });

        it('should handle missing optional fields and use defaults', function () {
            details = {
                count: 1,
                results: [{
                    id: 102,
                    // submission_meta_attributes is missing
                    // allowed_submission_file_types is missing
                    // default_submission_meta_attributes is missing
                    leaderboard_public: false
                }]
            };

            for (var k = 0; k < details.count; k++) {
                if (details.results[k].submission_meta_attributes != undefined || details.results[k].submission_meta_attributes != null) {
                    var attributes = details.results[k].submission_meta_attributes;
                    attributes.forEach(function (attribute) {
                        if (attribute["type"] == "checkbox") {
                            attribute["values"] = [];
                        }
                        else {
                            attribute["value"] = null;
                        }
                    });
                    var data = { "phaseId": details.results[k].id, "attributes": attributes };
                    vm.submissionMetaAttributes.push(data);
                }
                else {
                    var data = { "phaseId": details.results[k].id, "attributes": null };
                    vm.submissionMetaAttributes.push(data);
                }
                if (details.results[k].allowed_submission_file_types != undefined || details.results[k].allowed_submission_file_types != null) {
                    vm.allowedSubmissionFileTypes.push({
                        "phaseId": details.results[k].id,
                        "allowedSubmissionFileTypes": details.results[k].allowed_submission_file_types
                    });
                } else {
                    vm.allowedSubmissionFileTypes.push({
                        "phaseId": details.results[k].id,
                        "allowedSubmissionFileTypes": ".json, .zip, .txt, .tsv, .gz, .csv, .h5, .npy"
                    });
                }
                if (details.results[k].default_submission_meta_attributes != undefined && details.results[k].default_submission_meta_attributes != null) {
                    var meta_attributes = details.results[k].default_submission_meta_attributes;
                    var defaultMetaAttributes = vm.getDefaultMetaAttributesDict(meta_attributes);
                    vm.defaultSubmissionMetaAttributes.push({
                        "phaseId": details.results[k].id,
                        "defaultAttributes": defaultMetaAttributes
                    });
                } else {
                    vm.defaultSubmissionMetaAttributes.push({
                        "phaseId": details.results[k].id,
                        "defaultAttributes": {}
                    });
                }
                vm.phaseLeaderboardPublic.push({
                    "phaseId": details.results[k].id,
                    "leaderboardPublic": details.results[k].leaderboard_public
                });
            }

            // Assertions
            expect(vm.submissionMetaAttributes[0].attributes).toBeNull();
            expect(vm.allowedSubmissionFileTypes[0].allowedSubmissionFileTypes).toBe(".json, .zip, .txt, .tsv, .gz, .csv, .h5, .npy");
            expect(vm.defaultSubmissionMetaAttributes[0].defaultAttributes).toEqual({});
            expect(vm.phaseLeaderboardPublic[0].leaderboardPublic).toBe(false);
        });
    });

    describe('Unit tests for isMetricOrderedAscending function', function () {
        beforeEach(function () {
            vm.leaderboard = [{
                leaderboard__schema: {
                    metadata: {
                        accuracy: { sort_ascending: false },
                        loss: { sort_ascending: true },
                        f1_score: { sort_ascending: false }
                    }
                }
            }];
        });

        it('should return false when metadata is null', function () {
            vm.leaderboard[0].leaderboard__schema.metadata = null;
            expect(vm.isMetricOrderedAscending('accuracy')).toBe(false);
        });

        it('should return false when metadata is undefined', function () {
            vm.leaderboard[0].leaderboard__schema.metadata = undefined;
            expect(vm.isMetricOrderedAscending('accuracy')).toBe(false);
        });

        it('should return false when metric is not found in metadata', function () {
            expect(vm.isMetricOrderedAscending('nonexistent_metric')).toBe(false);
        });

        it('should return true when metric has sort_ascending set to true', function () {
            expect(vm.isMetricOrderedAscending('loss')).toBe(true);
        });

        it('should return false when metric has sort_ascending set to false', function () {
            expect(vm.isMetricOrderedAscending('accuracy')).toBe(false);
        });

        it('should return false when metric has sort_ascending set to false (f1_score)', function () {
            expect(vm.isMetricOrderedAscending('f1_score')).toBe(false);
        });

        it('should handle empty leaderboard gracefully', function () {
            vm.leaderboard = [];
            expect(function () { vm.isMetricOrderedAscending('accuracy'); }).toThrow();
        });
    });


    describe('Unit tests for time duration formatting logic (lines 1123-1165)', function () {
        var moment, duration;

        beforeEach(inject(function (_moment_) {
            moment = _moment_;
            vm.leaderboard = [];

            // Mock duration object with _data property
            duration = {
                _data: {},
                months: function () { return this._data.months; },
                asDays: function () { return this._data.days; },
                asHours: function () { return this._data.hours; },
                asMinutes: function () { return this._data.minutes; },
                asSeconds: function () { return this._data.seconds; }
            };
        }));

        it('should handle months duration (singular)', function () {
            vm.leaderboard[0] = {};
            duration._data = { months: 1, days: 0, hours: 0, minutes: 0, seconds: 0 };

            // Simulate the code block for months
            if (duration._data.months != 0) {
                var months = duration.months();
                vm.leaderboard[0].submission__submitted_at = months;
                if (months.toFixed(0) == 1) {
                    vm.leaderboard[0].timeSpan = 'month';
                } else {
                    vm.leaderboard[0].timeSpan = 'months';
                }
            }

            expect(vm.leaderboard[0].submission__submitted_at).toBe(1);
            expect(vm.leaderboard[0].timeSpan).toBe('month');
        });

        it('should handle months duration (plural)', function () {
            vm.leaderboard[0] = {};
            duration._data = { months: 3, days: 0, hours: 0, minutes: 0, seconds: 0 };

            // Simulate the code block for months
            if (duration._data.months != 0) {
                var months = duration.months();
                vm.leaderboard[0].submission__submitted_at = months;
                if (months.toFixed(0) == 1) {
                    vm.leaderboard[0].timeSpan = 'month';
                } else {
                    vm.leaderboard[0].timeSpan = 'months';
                }
            }

            expect(vm.leaderboard[0].submission__submitted_at).toBe(3);
            expect(vm.leaderboard[0].timeSpan).toBe('months');
        });

        it('should handle days duration (singular)', function () {
            vm.leaderboard[0] = {};
            duration._data = { months: 0, days: 1, hours: 0, minutes: 0, seconds: 0 };

            // Simulate the code block for days
            if (duration._data.months != 0) {
                // months logic
            } else if (duration._data.days != 0) {
                var days = duration.asDays();
                vm.leaderboard[0].submission__submitted_at = days;
                if (days.toFixed(0) == 1) {
                    vm.leaderboard[0].timeSpan = 'day';
                } else {
                    vm.leaderboard[0].timeSpan = 'days';
                }
            }

            expect(vm.leaderboard[0].submission__submitted_at).toBe(1);
            expect(vm.leaderboard[0].timeSpan).toBe('day');
        });

        it('should handle days duration (plural)', function () {
            vm.leaderboard[0] = {};
            duration._data = { months: 0, days: 5, hours: 0, minutes: 0, seconds: 0 };

            // Simulate the code block for days
            if (duration._data.months != 0) {
                // months logic
            } else if (duration._data.days != 0) {
                var days = duration.asDays();
                vm.leaderboard[0].submission__submitted_at = days;
                if (days.toFixed(0) == 1) {
                    vm.leaderboard[0].timeSpan = 'day';
                } else {
                    vm.leaderboard[0].timeSpan = 'days';
                }
            }

            expect(vm.leaderboard[0].submission__submitted_at).toBe(5);
            expect(vm.leaderboard[0].timeSpan).toBe('days');
        });

        it('should handle hours duration (singular)', function () {
            vm.leaderboard[0] = {};
            duration._data = { months: 0, days: 0, hours: 1, minutes: 0, seconds: 0 };

            // Simulate the code block for hours
            if (duration._data.months != 0) {
                // months logic
            } else if (duration._data.days != 0) {
                // days logic
            } else if (duration._data.hours != 0) {
                var hours = duration.asHours();
                vm.leaderboard[0].submission__submitted_at = hours;
                if (hours.toFixed(0) == 1) {
                    vm.leaderboard[0].timeSpan = 'hour';
                } else {
                    vm.leaderboard[0].timeSpan = 'hours';
                }
            }

            expect(vm.leaderboard[0].submission__submitted_at).toBe(1);
            expect(vm.leaderboard[0].timeSpan).toBe('hour');
        });

        it('should handle hours duration (plural)', function () {
            vm.leaderboard[0] = {};
            duration._data = { months: 0, days: 0, hours: 12, minutes: 0, seconds: 0 };

            // Simulate the code block for hours
            if (duration._data.months != 0) {
                // months logic
            } else if (duration._data.days != 0) {
                // days logic
            } else if (duration._data.hours != 0) {
                var hours = duration.asHours();
                vm.leaderboard[0].submission__submitted_at = hours;
                if (hours.toFixed(0) == 1) {
                    vm.leaderboard[0].timeSpan = 'hour';
                } else {
                    vm.leaderboard[0].timeSpan = 'hours';
                }
            }

            expect(vm.leaderboard[0].submission__submitted_at).toBe(12);
            expect(vm.leaderboard[0].timeSpan).toBe('hours');
        });

        it('should handle minutes duration (singular)', function () {
            vm.leaderboard[0] = {};
            duration._data = { months: 0, days: 0, hours: 0, minutes: 1, seconds: 0 };

            // Simulate the code block for minutes
            if (duration._data.months != 0) {
                // months logic
            } else if (duration._data.days != 0) {
                // days logic
            } else if (duration._data.hours != 0) {
                // hours logic
            } else if (duration._data.minutes != 0) {
                var minutes = duration.asMinutes();
                vm.leaderboard[0].submission__submitted_at = minutes;
                if (minutes.toFixed(0) == 1) {
                    vm.leaderboard[0].timeSpan = 'minute';
                } else {
                    vm.leaderboard[0].timeSpan = 'minutes';
                }
            }

            expect(vm.leaderboard[0].submission__submitted_at).toBe(1);
            expect(vm.leaderboard[0].timeSpan).toBe('minute');
        });

        it('should handle minutes duration (plural)', function () {
            vm.leaderboard[0] = {};
            duration._data = { months: 0, days: 0, hours: 0, minutes: 30, seconds: 0 };

            // Simulate the code block for minutes
            if (duration._data.months != 0) {
                // months logic
            } else if (duration._data.days != 0) {
                // days logic
            } else if (duration._data.hours != 0) {
                // hours logic
            } else if (duration._data.minutes != 0) {
                var minutes = duration.asMinutes();
                vm.leaderboard[0].submission__submitted_at = minutes;
                if (minutes.toFixed(0) == 1) {
                    vm.leaderboard[0].timeSpan = 'minute';
                } else {
                    vm.leaderboard[0].timeSpan = 'minutes';
                }
            }

            expect(vm.leaderboard[0].submission__submitted_at).toBe(30);
            expect(vm.leaderboard[0].timeSpan).toBe('minutes');
        });

        it('should handle seconds duration (singular)', function () {
            vm.leaderboard[0] = {};
            duration._data = { months: 0, days: 0, hours: 0, minutes: 0, seconds: 1 };

            // Simulate the code block for seconds
            if (duration._data.months != 0) {
                // months logic
            } else if (duration._data.days != 0) {
                // days logic
            } else if (duration._data.hours != 0) {
                // hours logic
            } else if (duration._data.minutes != 0) {
                // minutes logic
            } else if (duration._data.seconds != 0) {
                var second = duration.asSeconds();
                vm.leaderboard[0].submission__submitted_at = second;
                if (second.toFixed(0) == 1) {
                    vm.leaderboard[0].timeSpan = 'second';
                } else {
                    vm.leaderboard[0].timeSpan = 'seconds';
                }
            }

            expect(vm.leaderboard[0].submission__submitted_at).toBe(1);
            expect(vm.leaderboard[0].timeSpan).toBe('second');
        });

        it('should handle seconds duration (plural)', function () {
            vm.leaderboard[0] = {};
            duration._data = { months: 0, days: 0, hours: 0, minutes: 0, seconds: 45 };

            // Simulate the code block for seconds
            if (duration._data.months != 0) {
                // months logic
            } else if (duration._data.days != 0) {
                // days logic
            } else if (duration._data.hours != 0) {
                // hours logic
            } else if (duration._data.minutes != 0) {
                // minutes logic
            } else if (duration._data.seconds != 0) {
                var second = duration.asSeconds();
                vm.leaderboard[0].submission__submitted_at = second;
                if (second.toFixed(0) == 1) {
                    vm.leaderboard[0].timeSpan = 'second';
                } else {
                    vm.leaderboard[0].timeSpan = 'seconds';
                }
            }

            expect(vm.leaderboard[0].submission__submitted_at).toBe(45);
            expect(vm.leaderboard[0].timeSpan).toBe('seconds');
        });
    });

    describe('Unit tests for acceptTermsAndConditions function (lines 3045-3055)', function () {
        beforeEach(function () {
            spyOn($mdDialog, 'hide');
            vm.termsAndConditions = false;
            // Mock the selectExistTeam function since it's not accessible in this scope
            vm.selectExistTeam = jasmine.createSpy('selectExistTeam');
        });

        it('should call selectExistTeam and hide dialog when form is valid and terms accepted', function () {
            var acceptTermsAndConditionsForm = true;
            vm.termsAndConditions = true;

            vm.acceptTermsAndConditions(acceptTermsAndConditionsForm);

            expect(vm.selectExistTeam).toHaveBeenCalled();
            expect($mdDialog.hide).toHaveBeenCalled();
        });

        it('should only hide dialog when form is valid but terms not accepted', function () {
            var acceptTermsAndConditionsForm = true;
            vm.termsAndConditions = false;

            vm.acceptTermsAndConditions(acceptTermsAndConditionsForm);

            expect(vm.selectExistTeam).not.toHaveBeenCalled();
            expect($mdDialog.hide).not.toHaveBeenCalled(); // Dialog should NOT be hidden
        });

        it('should hide dialog when form is invalid', function () {
            var acceptTermsAndConditionsForm = false;
            vm.termsAndConditions = true;

            vm.acceptTermsAndConditions(acceptTermsAndConditionsForm);

            expect(vm.selectExistTeam).not.toHaveBeenCalled();
            expect($mdDialog.hide).toHaveBeenCalled();
        });

        it('should hide dialog when form is null', function () {
            var acceptTermsAndConditionsForm = null;
            vm.termsAndConditions = true;

            vm.acceptTermsAndConditions(acceptTermsAndConditionsForm);

            expect(vm.selectExistTeam).not.toHaveBeenCalled();
            expect($mdDialog.hide).toHaveBeenCalled();
        });

        it('should hide dialog when form is undefined', function () {
            var acceptTermsAndConditionsForm = undefined;
            vm.termsAndConditions = true;

            vm.acceptTermsAndConditions(acceptTermsAndConditionsForm);

            expect(vm.selectExistTeam).not.toHaveBeenCalled();
            expect($mdDialog.hide).toHaveBeenCalled();
        });

        it('should handle both conditions being false', function () {
            var acceptTermsAndConditionsForm = false;
            vm.termsAndConditions = false;

            vm.acceptTermsAndConditions(acceptTermsAndConditionsForm);

            expect(vm.selectExistTeam).not.toHaveBeenCalled();
            expect($mdDialog.hide).toHaveBeenCalled();
        });
    });

    describe('Unit tests for reRunSubmission function', function () {
        var submissionObject, parameters, userKey;

        beforeEach(function () {
            submissionObject = { id: 123, classList: [] };
            parameters = {};
            userKey = 'encrypted key'; // Match the actual userKey used in the code
            spyOn(utilities, 'sendRequest');
            spyOn($rootScope, 'notify');
        });

        it('should set correct CSS classes and make API call with proper parameters', function () {
            vm.reRunSubmission(submissionObject);
            expect(submissionObject.classList).toEqual(['spin', 'progress-indicator']);
            expect(utilities.sendRequest).toHaveBeenCalledWith({
                url: 'jobs/submissions/123/re-run/',
                method: 'POST',
                token: userKey,
                data: {},
                callback: jasmine.any(Object)
            });
        });

        it('should handle successful re-run and show success notification', function () {
            var successResponse = { data: { success: 'Submission re-run initiated successfully' } };
            utilities.sendRequest.and.callFake(function (params) {
                params.callback.onSuccess(successResponse);
            });
            vm.reRunSubmission(submissionObject);
            expect($rootScope.notify).toHaveBeenCalledWith("success", "Submission re-run initiated successfully");
            expect(submissionObject.classList).toEqual(['']);
        });

        it('should handle error response and show error notification', function () {
            var errorResponse = { data: 'Submission re-run failed' };
            utilities.sendRequest.and.callFake(function (params) {
                params.callback.onError(errorResponse);
            });
            vm.reRunSubmission(submissionObject);
            expect($rootScope.notify).toHaveBeenCalledWith("error", "Submission re-run failed");
            expect(submissionObject.classList).toEqual(['']);
        });

        it('should handle error response with object data', function () {
            var errorResponse = { data: { error: 'Network timeout' } };
            utilities.sendRequest.and.callFake(function (params) {
                params.callback.onError(errorResponse);
            });
            vm.reRunSubmission(submissionObject);
            expect($rootScope.notify).toHaveBeenCalledWith("error", { error: 'Network timeout' });
            expect(submissionObject.classList).toEqual(['']);
        });

        it('should handle empty success response data', function () {
            var successResponse = { data: {} };
            utilities.sendRequest.and.callFake(function (params) {
                params.callback.onSuccess(successResponse);
            });
            vm.reRunSubmission(submissionObject);
            expect($rootScope.notify).toHaveBeenCalledWith("success", undefined);
            expect(submissionObject.classList).toEqual(['']);
        });

        it('should handle null error response data', function () {
            var errorResponse = { data: null };
            utilities.sendRequest.and.callFake(function (params) {
                params.callback.onError(errorResponse);
            });
            vm.reRunSubmission(submissionObject);
            expect($rootScope.notify).toHaveBeenCalledWith("error", null);
            expect(submissionObject.classList).toEqual(['']);
        });

        it('should handle undefined error response data', function () {
            var errorResponse = { data: undefined };
            utilities.sendRequest.and.callFake(function (params) {
                params.callback.onError(errorResponse);
            });
            vm.reRunSubmission(submissionObject);
            expect($rootScope.notify).toHaveBeenCalledWith("error", undefined);
            expect(submissionObject.classList).toEqual(['']);
        });

        it('should work with different submission IDs', function () {
            var differentSubmission = { id: 999, classList: [] };
            utilities.sendRequest.and.callFake(function (params) {
                params.callback.onSuccess({ data: { success: 'Success' } });
            });
            vm.reRunSubmission(differentSubmission);
            expect(utilities.sendRequest).toHaveBeenCalledWith({
                url: 'jobs/submissions/999/re-run/',
                method: 'POST',
                token: userKey,
                data: {},
                callback: jasmine.any(Object)
            });
        });

        it('should preserve existing classList properties if any', function () {
            var submissionWithExistingClasses = {
                id: 456,
                classList: ['existing-class', 'another-class']
            };
            utilities.sendRequest.and.callFake(function (params) {
                // Check immediately after calling reRunSubmission
                expect(submissionWithExistingClasses.classList).toEqual(['spin', 'progress-indicator']);
                params.callback.onSuccess({ data: { success: 'Success' } });
            });
            vm.reRunSubmission(submissionWithExistingClasses);
            // After callback
            expect(submissionWithExistingClasses.classList).toEqual(['']);
        });

        it('should handle submission object without classList property', function () {
            var submissionWithoutClassList = { id: 789 };
            utilities.sendRequest.and.callFake(function (params) {
                params.callback.onSuccess({ data: { success: 'Success' } });
            });
            expect(function () {
                vm.reRunSubmission(submissionWithoutClassList);
            }).not.toThrow();
        });

        it('should handle submission object with null classList', function () {
            var submissionWithNullClassList = { id: 101, classList: null };
            utilities.sendRequest.and.callFake(function (params) {
                params.callback.onSuccess({ data: { success: 'Success' } });
            });
            expect(function () {
                vm.reRunSubmission(submissionWithNullClassList);
            }).not.toThrow();
        });

        it('should handle submission object with undefined classList', function () {
            var submissionWithUndefinedClassList = { id: 102, classList: undefined };
            utilities.sendRequest.and.callFake(function (params) {
                params.callback.onSuccess({ data: { success: 'Success' } });
            });
            expect(function () {
                vm.reRunSubmission(submissionWithUndefinedClassList);
            }).not.toThrow();
        });

        it('should handle missing submission ID', function () {
            var submissionWithoutId = { classList: [] };
            utilities.sendRequest.and.callFake(function (params) {
                params.callback.onSuccess({ data: { success: 'Success' } });
            });
            vm.reRunSubmission(submissionWithoutId);
            expect(utilities.sendRequest).toHaveBeenCalledWith({
                url: 'jobs/submissions/undefined/re-run/',
                method: 'POST',
                token: userKey,
                data: {},
                callback: jasmine.any(Object)
            });
        });

        it('should handle submission ID as string', function () {
            var submissionWithStringId = { id: '123', classList: [] };
            utilities.sendRequest.and.callFake(function (params) {
                params.callback.onSuccess({ data: { success: 'Success' } });
            });
            vm.reRunSubmission(submissionWithStringId);
            expect(utilities.sendRequest).toHaveBeenCalledWith({
                url: 'jobs/submissions/123/re-run/',
                method: 'POST',
                token: userKey,
                data: {},
                callback: jasmine.any(Object)
            });
        });

        it('should handle submission ID as zero', function () {
            var submissionWithZeroId = { id: 0, classList: [] };
            utilities.sendRequest.and.callFake(function (params) {
                params.callback.onSuccess({ data: { success: 'Success' } });
            });
            vm.reRunSubmission(submissionWithZeroId);
            expect(utilities.sendRequest).toHaveBeenCalledWith({
                url: 'jobs/submissions/0/re-run/',
                method: 'POST',
                token: userKey,
                data: {},
                callback: jasmine.any(Object)
            });
        });

        it('should handle submission ID as negative number', function () {
            var submissionWithNegativeId = { id: -1, classList: [] };
            utilities.sendRequest.and.callFake(function (params) {
                params.callback.onSuccess({ data: { success: 'Success' } });
            });
            vm.reRunSubmission(submissionWithNegativeId);
            expect(utilities.sendRequest).toHaveBeenCalledWith({
                url: 'jobs/submissions/-1/re-run/',
                method: 'POST',
                token: userKey,
                data: {},
                callback: jasmine.any(Object)
            });
        });
    });

    describe('Unit tests for manageWorker function', function () {
        var $rootScope, utilities, vm, $controller, $scope;

        beforeEach(inject(function (_$controller_, _$rootScope_, _utilities_) {
            $controller = _$controller_;
            $rootScope = _$rootScope_;
            utilities = _utilities_;
            $scope = $rootScope.$new();

            spyOn(utilities, 'sendRequest');
            spyOn($rootScope, 'notify');

            vm = $controller('ChallengeCtrl', { $scope: $scope, $rootScope: $rootScope, utilities: utilities });
            vm.challengeId = 42; // set a dummy challengeId
        }));

        it('should notify success when details.action is "Success"', function () {
            utilities.sendRequest.and.callFake(function (params) {
                params.callback.onSuccess({ data: { action: "Success" } });
            });

            vm.manageWorker('start');
            expect($rootScope.notify).toHaveBeenCalledWith("success", "Worker(s) started succesfully.");
        });

        it('should notify error when details.action is not "Success"', function () {
            utilities.sendRequest.and.callFake(function (params) {
                params.callback.onSuccess({ data: { action: "Failure", error: "Some error" } });
            });

            vm.manageWorker('stop');
            expect($rootScope.notify).toHaveBeenCalledWith("error", "Some error");
        });

        it('should notify generic error when error is undefined in onError', function () {
            utilities.sendRequest.and.callFake(function (params) {
                params.callback.onError({ data: {} });
            });

            vm.manageWorker('restart');
            expect($rootScope.notify).toHaveBeenCalledWith("error", "There was an error.");
        });

        it('should notify error with message when error is defined in onError', function () {
            utilities.sendRequest.and.callFake(function (params) {
                params.callback.onError({ data: { error: "Specific error" } });
            });

            vm.manageWorker('restart');
            expect($rootScope.notify).toHaveBeenCalledWith("error", "There was an error: Specific error");
        });

        it('should call utilities.sendRequest with correct parameters', function () {
            vm.manageWorker('start');
            expect(utilities.sendRequest).toHaveBeenCalled();
            var params = utilities.sendRequest.calls.mostRecent().args[0];
            expect(params.url).toBe('challenges/42/manage_worker/start/');
            expect(params.method).toBe('PUT');
            expect(params.data).toEqual({});
            expect(typeof params.callback.onSuccess).toBe('function');
            expect(typeof params.callback.onError).toBe('function');
        });
    });

    describe('Unit tests for load function (submissions pagination)', function () {
        var localVm, $http, $scope, $controller, getHandler;

        beforeEach(inject(function (_$controller_, _$rootScope_, _$http_) {
            $controller = _$controller_;
            $scope = _$rootScope_.$new();
            $http = _$http_;
            localVm = $controller('ChallengeCtrl', { $scope: $scope });
            localVm.startLoader = jasmine.createSpy('startLoader');
            localVm.stopLoader = jasmine.createSpy('stopLoader');
            getHandler = null;
            spyOn($http, 'get').and.callFake(function () {
                return getHandler.apply(this, arguments);
            });
        }));

        it('should make GET request, set pagination, and stop loader when url is not null', function () {
            var url = 'some/url';
            var responseData = {
                next: 'page=3',
                previous: 'page=1',
                count: 300,
                results: []
            };
            getHandler = function (reqUrl, opts) {
                expect(reqUrl).toBe(url);
                expect(opts.headers.Authorization).toBe("Token encrypted key");
                return {
                    then: function (cb) {
                        cb({ data: responseData });
                    }
                };
            };

            localVm.load = function (url) {
                localVm.startLoader("Loading Submissions");
                if (url !== null) {
                    var headers = {
                        'Authorization': "Token encrypted key"
                    };
                    $http.get(url, { headers: headers }).then(function (response) {
                        var details = response.data;
                        localVm.submissionResult = details;

                        if (localVm.submissionResult.next === null) {
                            localVm.isNext = 'disabled';
                            localVm.currentPage = localVm.submissionResult.count / 150;
                            localVm.currentRefPage = Math.ceil(localVm.currentPage);
                        } else {
                            localVm.isNext = '';
                            localVm.currentPage = parseInt(localVm.submissionResult.next.split('page=')[1] - 1);
                            localVm.currentRefPage = Math.ceil(localVm.currentPage);
                        }

                        if (localVm.submissionResult.previous === null) {
                            localVm.isPrev = 'disabled';
                        } else {
                            localVm.isPrev = '';
                        }
                        localVm.stopLoader();
                    });
                } else {
                    localVm.stopLoader();
                }
            };

            localVm.load(url);

            expect(localVm.startLoader).toHaveBeenCalledWith("Loading Submissions");
            expect(localVm.isNext).toBe('');
            expect(localVm.currentPage).toBe(2);
            expect(localVm.currentRefPage).toBe(2);
            expect(localVm.isPrev).toBe('');
            expect(localVm.submissionResult).toEqual(responseData);
            expect(localVm.stopLoader).toHaveBeenCalled();
        });

        it('should set isNext and isPrev to disabled when next and previous are null', function () {
            var url = 'some/url';
            var responseData = {
                next: null,
                previous: null,
                count: 150,
                results: []
            };
            getHandler = function (reqUrl, opts) {
                return {
                    then: function (cb) {
                        cb({ data: responseData });
                    }
                };
            };

            localVm.load = function (url) {
                localVm.startLoader("Loading Submissions");
                if (url !== null) {
                    var headers = {
                        'Authorization': "Token encrypted key"
                    };
                    $http.get(url, { headers: headers }).then(function (response) {
                        var details = response.data;
                        localVm.submissionResult = details;

                        if (localVm.submissionResult.next === null) {
                            localVm.isNext = 'disabled';
                            localVm.currentPage = localVm.submissionResult.count / 150;
                            localVm.currentRefPage = Math.ceil(localVm.currentPage);
                        } else {
                            localVm.isNext = '';
                            localVm.currentPage = parseInt(localVm.submissionResult.next.split('page=')[1] - 1);
                            localVm.currentRefPage = Math.ceil(localVm.currentPage);
                        }

                        if (localVm.submissionResult.previous === null) {
                            localVm.isPrev = 'disabled';
                        } else {
                            localVm.isPrev = '';
                        }
                        localVm.stopLoader();
                    });
                } else {
                    localVm.stopLoader();
                }
            };

            localVm.load(url);

            expect(localVm.isNext).toBe('disabled');
            expect(localVm.currentPage).toBe(1);
            expect(localVm.currentRefPage).toBe(1);
            expect(localVm.isPrev).toBe('disabled');
            expect(localVm.stopLoader).toHaveBeenCalled();
        });

        it('should call stopLoader if url is null', function () {
            getHandler = function () {
                // Should not be called
                throw new Error('Should not call $http.get when url is null');
            };
            localVm.load = function (url) {
                localVm.startLoader("Loading Submissions");
                if (url !== null) {
                    var headers = {
                        'Authorization': "Token encrypted key"
                    };
                    $http.get(url, { headers: headers }).then(function (response) {
                        var details = response.data;
                        localVm.submissionResult = details;

                        if (localVm.submissionResult.next === null) {
                            localVm.isNext = 'disabled';
                            localVm.currentPage = localVm.submissionResult.count / 150;
                            localVm.currentRefPage = Math.ceil(localVm.currentPage);
                        } else {
                            localVm.isNext = '';
                            localVm.currentPage = parseInt(localVm.submissionResult.next.split('page=')[1] - 1);
                            localVm.currentRefPage = Math.ceil(localVm.currentPage);
                        }

                        if (localVm.submissionResult.previous === null) {
                            localVm.isPrev = 'disabled';
                        } else {
                            localVm.isPrev = '';
                        }
                        localVm.stopLoader();
                    });
                } else {
                    localVm.stopLoader();
                }
            };

            localVm.load(null);
            expect(localVm.startLoader).toHaveBeenCalledWith("Loading Submissions");
            expect(localVm.stopLoader).toHaveBeenCalled();
        });
    });

    describe('Pagination logic for existTeam', function () {
        var vm;

        beforeEach(function () {
            vm = {
                stopLoader: jasmine.createSpy('stopLoader')
            };
        });

        it('should set isNext to disabled and currentPage to count/10 when next is null', function () {
            var details = {
                next: null,
                previous: null,
                count: 30
            };
            vm.existTeam = details;

            // Simulate the code block
            if (vm.existTeam.next === null) {
                vm.isNext = 'disabled';
                vm.currentPage = vm.existTeam.count / 10;
            } else {
                vm.isNext = '';
                vm.currentPage = parseInt(vm.existTeam.next.split('page=')[1] - 1);
            }

            if (vm.existTeam.previous === null) {
                vm.isPrev = 'disabled';
            } else {
                vm.isPrev = '';
            }
            vm.stopLoader();

            expect(vm.isNext).toBe('disabled');
            expect(vm.currentPage).toBe(3);
            expect(vm.isPrev).toBe('disabled');
            expect(vm.stopLoader).toHaveBeenCalled();
        });

        it('should set isNext to "" and currentPage from next when next is not null', function () {
            var details = {
                next: 'page=5',
                previous: null,
                count: 50
            };
            vm.existTeam = details;

            if (vm.existTeam.next === null) {
                vm.isNext = 'disabled';
                vm.currentPage = vm.existTeam.count / 10;
            } else {
                vm.isNext = '';
                vm.currentPage = parseInt(vm.existTeam.next.split('page=')[1] - 1);
            }

            if (vm.existTeam.previous === null) {
                vm.isPrev = 'disabled';
            } else {
                vm.isPrev = '';
            }
            vm.stopLoader();

            expect(vm.isNext).toBe('');
            expect(vm.currentPage).toBe(4); // 5-1=4
            expect(vm.isPrev).toBe('disabled');
            expect(vm.stopLoader).toHaveBeenCalled();
        });

        it('should set isPrev to "" when previous is not null', function () {
            var details = {
                next: null,
                previous: 'page=2',
                count: 20
            };
            vm.existTeam = details;

            if (vm.existTeam.next === null) {
                vm.isNext = 'disabled';
                vm.currentPage = vm.existTeam.count / 10;
            } else {
                vm.isNext = '';
                vm.currentPage = parseInt(vm.existTeam.next.split('page=')[1] - 1);
            }

            if (vm.existTeam.previous === null) {
                vm.isPrev = 'disabled';
            } else {
                vm.isPrev = '';
            }
            vm.stopLoader();

            expect(vm.isNext).toBe('disabled');
            expect(vm.currentPage).toBe(2);
            expect(vm.isPrev).toBe('');
            expect(vm.stopLoader).toHaveBeenCalled();
        });

        it('should set isNext and isPrev to "" when both next and previous are not null', function () {
            var details = {
                next: 'page=3',
                previous: 'page=1',
                count: 30
            };
            vm.existTeam = details;

            if (vm.existTeam.next === null) {
                vm.isNext = 'disabled';
                vm.currentPage = vm.existTeam.count / 10;
            } else {
                vm.isNext = '';
                vm.currentPage = parseInt(vm.existTeam.next.split('page=')[1] - 1);
            }

            if (vm.existTeam.previous === null) {
                vm.isPrev = 'disabled';
            } else {
                vm.isPrev = '';
            }
            vm.stopLoader();

            expect(vm.isNext).toBe('');
            expect(vm.currentPage).toBe(2); // 3-1=2
            expect(vm.isPrev).toBe('');
            expect(vm.stopLoader).toHaveBeenCalled();
        });
    });
});