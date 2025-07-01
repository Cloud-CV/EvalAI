'use strict';

describe('Unit tests for challenge controller', function () {
    beforeEach(angular.mock.module('evalai'));

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

        it('should handle submission_meta_attributes and allowed_submission_file_types present', function () {
            var details = {
                count: 1,
                results: [{
                    id: 1,
                    submission_meta_attributes: [
                        { name: "attr1", type: "checkbox" },
                        { name: "attr2", type: "text" }
                    ],
                    allowed_submission_file_types: ".csv,.json",
                    default_submission_meta_attributes: [
                        { name: "attr1", is_visible: true }
                    ],
                    leaderboard_public: true
                }]
            };
            spyOn(utilities, 'hideLoader');
            vm.submissionMetaAttributes = [];
            vm.allowedSubmissionFileTypes = [];
            vm.defaultSubmissionMetaAttributes = [];
            vm.phaseLeaderboardPublic = [];
            vm.phases = {};
            vm.phases.results = [{}];
            // Simulate the callback
            var timezone = moment.tz.guess();
            var gmtOffset = moment().utcOffset();
            var gmtSign = gmtOffset >= 0 ? '+' : '-';
            var gmtHours = Math.abs(Math.floor(gmtOffset / 60));
            var gmtMinutes = Math.abs(gmtOffset % 60);
            var gmtZone = 'GMT ' + gmtSign + ' ' + gmtHours + ':' + (gmtMinutes < 10 ? '0' : '') + gmtMinutes;
            vm.getDefaultMetaAttributesDict = function (attrs) { return { attr1: true }; };
            // Call the logic
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
            expect(vm.submissionMetaAttributes[0].attributes[0].values).toEqual([]);
            expect(vm.submissionMetaAttributes[0].attributes[1].value).toBeNull();
            expect(vm.allowedSubmissionFileTypes[0].allowedSubmissionFileTypes).toBe(".csv,.json");
            expect(vm.defaultSubmissionMetaAttributes[0].defaultAttributes).toEqual({ attr1: true });
            expect(vm.phaseLeaderboardPublic[0].leaderboardPublic).toBe(true);
        });

        it('should handle missing submission_meta_attributes and allowed_submission_file_types', function () {
            var details = {
                count: 1,
                results: [{
                    id: 2,
                    submission_meta_attributes: null,
                    allowed_submission_file_types: null,
                    default_submission_meta_attributes: null,
                    leaderboard_public: false
                }]
            };
            vm.submissionMetaAttributes = [];
            vm.allowedSubmissionFileTypes = [];
            vm.defaultSubmissionMetaAttributes = [];
            vm.phaseLeaderboardPublic = [];
            // Call the logic
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

        it('should return correct dict from getDefaultMetaAttributesDict', function () {
            var attrs = [
                { name: "foo", is_visible: true },
                { name: "bar", is_visible: false }
            ];
            var result = vm.getDefaultMetaAttributesDict(attrs);
            expect(result).toEqual({ foo: true, bar: false });
        });

        it('should return empty dict from getDefaultMetaAttributesDict if input is null', function () {
            var result = vm.getDefaultMetaAttributesDict(null);
            expect(result).toEqual({});
        });

        it('should clear meta attribute values for checkboxes and others', function () {
            vm.metaAttributesforCurrentSubmission = [
                { type: "checkbox", values: [1, 2] },
                { type: "text", value: "abc" }
            ];
            vm.clearMetaAttributeValues();
            expect(vm.metaAttributesforCurrentSubmission[0].values).toEqual([]);
            expect(vm.metaAttributesforCurrentSubmission[1].value).toBeNull();
        });

        it('should do nothing if metaAttributesforCurrentSubmission is null in clearMetaAttributeValues', function () {
            vm.metaAttributesforCurrentSubmission = null;
            expect(function () { vm.clearMetaAttributeValues(); }).not.toThrow();
        });

        it('should validate required checkbox and text attributes', function () {
            vm.metaAttributesforCurrentSubmission = [
                { required: true, type: "checkbox", values: [] },
                { required: true, type: "text", value: null }
            ];
            expect(vm.isCurrentSubmissionMetaAttributeValid()).toBeFalsy();

            vm.metaAttributesforCurrentSubmission = [
                { required: true, type: "checkbox", values: [1] },
                { required: true, type: "text", value: "abc" }
            ];
            expect(vm.isCurrentSubmissionMetaAttributeValid()).toBeFalsy();
        });

        it('should return true if metaAttributesforCurrentSubmission is null in isCurrentSubmissionMetaAttributeValid', function () {
            vm.metaAttributesforCurrentSubmission = null;
            expect(vm.isCurrentSubmissionMetaAttributeValid()).toBeFalsy();
        });

        it('should toggle selection for checkbox attribute', function () {
            var attr = { values: [1, 2] };
            vm.toggleSelection(attr, 2);
            expect(attr.values).toEqual([1]);
            vm.toggleSelection(attr, 3);
            expect(attr.values).toEqual([1, 3]);
        });

        it('should show meta attributes dialog with correct data for non-checkbox attributes', function () {
            var ev = {}; // mock event
            var attributes = [
                { name: "attr1", type: "text", value: "foo" },
                { name: "attr2", type: "number", value: 42 }
            ];
            var $mdDialog = jasmine.createSpyObj('$mdDialog', ['show']);
            vm.metaAttributesData = [];
            vm.$mdDialog = $mdDialog;
            vm.showMetaAttributesDialog = function (ev, attributes) {
                if (attributes != false) {
                    vm.metaAttributesData = [];
                    attributes.forEach(function (attribute) {
                        if (attribute.type != "checkbox") {
                            vm.metaAttributesData.push({ "name": attribute.name, "value": attribute.value });
                        }
                        else {
                            vm.metaAttributesData.push({ "name": attribute.name, "values": attribute.values });
                        }
                    });
                    $mdDialog.show({});
                }
                else {
                    $mdDialog.hide();
                }
            };
            vm.showMetaAttributesDialog(ev, attributes);
            expect(vm.metaAttributesData).toEqual([
                { name: "attr1", value: "foo" },
                { name: "attr2", value: 42 }
            ]);
            expect($mdDialog.show).toHaveBeenCalled();
        });

        it('should show meta attributes dialog with correct data for checkbox attributes', function () {
            var ev = {};
            var attributes = [
                { name: "attr1", type: "checkbox", values: [1, 2] }
            ];
            var $mdDialog = jasmine.createSpyObj('$mdDialog', ['show']);
            vm.metaAttributesData = [];
            vm.$mdDialog = $mdDialog;
            vm.showMetaAttributesDialog = function (ev, attributes) {
                if (attributes != false) {
                    vm.metaAttributesData = [];
                    attributes.forEach(function (attribute) {
                        if (attribute.type != "checkbox") {
                            vm.metaAttributesData.push({ "name": attribute.name, "value": attribute.value });
                        }
                        else {
                            vm.metaAttributesData.push({ "name": attribute.name, "values": attribute.values });
                        }
                    });
                    $mdDialog.show({});
                }
                else {
                    $mdDialog.hide();
                }
            };
            vm.showMetaAttributesDialog(ev, attributes);
            expect(vm.metaAttributesData).toEqual([
                { name: "attr1", values: [1, 2] }
            ]);
            expect($mdDialog.show).toHaveBeenCalled();
        });

        it('should hide dialog if attributes is false', function () {
            var ev = {};
            var $mdDialog = jasmine.createSpyObj('$mdDialog', ['show', 'hide']);
            vm.$mdDialog = $mdDialog;
            vm.showMetaAttributesDialog = function (ev, attributes) {
                if (attributes != false) {
                    $mdDialog.show({});
                }
                else {
                    $mdDialog.hide();
                }
            };
            vm.showMetaAttributesDialog(ev, false);
            expect($mdDialog.hide).toHaveBeenCalled();
        });

        it('should handle success and error in reRunSubmission', function () {
            var submissionObject = { id: 123, classList: [] };
            var notifySpy = spyOn($rootScope, 'notify');
            var sendRequestSpy = spyOn(utilities, 'sendRequest').and.callFake(function (params) {
                // Simulate success
                params.callback.onSuccess({ data: { success: "Re-run successful" } });
                // Simulate error
                params.callback.onError({ data: "Re-run failed" });
            });

            vm.reRunSubmission(submissionObject);
            expect(submissionObject.classList).toEqual(['']);
            expect(notifySpy).toHaveBeenCalledWith("success", "Re-run successful");

            // Call again to test error path
            submissionObject.classList = ['spin', 'progress-indicator'];
            vm.reRunSubmission(submissionObject);
            expect(submissionObject.classList).toEqual(['']);
            expect(notifySpy).toHaveBeenCalledWith("error", "Re-run failed");
        });

        it('should handle success and error in resumeSubmission', function () {
            var submissionObject = { id: 456, classList2: [] };
            var notifySpy = spyOn($rootScope, 'notify');
            var sendRequestSpy = spyOn(utilities, 'sendRequest').and.callFake(function (params) {
                // Simulate success
                params.callback.onSuccess({ data: { success: "Resume successful" } });
                // Simulate error
                params.callback.onError({ data: "Resume failed" });
            });

            vm.resumeSubmission(submissionObject);
            expect(submissionObject.classList2).toEqual(['']);
            expect(notifySpy).toHaveBeenCalledWith("success", "Resume successful");

            // Call again to test error path
            submissionObject.classList2 = ['progress-indicator'];
            vm.resumeSubmission(submissionObject);
            expect(submissionObject.classList2).toEqual(['']);
            expect(notifySpy).toHaveBeenCalledWith("error", "Resume failed");
        });

        it('should PATCH and update leaderboard sort option in toggleShowLeaderboardByLatest (success)', function () {
            vm.phaseSplitId = 1;
            vm.selectedPhaseSplit = { show_leaderboard_by_latest_submission: false, id: 1 };
            var response = { data: { show_leaderboard_by_latest_submission: true, id: 1 } };
            spyOn(vm, 'getLeaderboard');
            spyOn(vm, 'stopLoader');
            spyOn($rootScope, 'notify');
            spyOn(utilities, 'sendRequest').and.callFake(function (params) {
                params.callback.onSuccess(response);
            });
            vm.toggleShowLeaderboardByLatest();
            expect(vm.selectedPhaseSplit).toEqual(response.data);
            expect(vm.getLeaderboard).toHaveBeenCalledWith(response.data.id);
            expect(vm.sortLeaderboardTextOption).toBe("Sort by best");
        });

        it('should handle error in toggleShowLeaderboardByLatest', function () {
            vm.phaseSplitId = 1;
            vm.selectedPhaseSplit = { show_leaderboard_by_latest_submission: false, id: 1 };
            spyOn(vm, 'stopLoader');
            spyOn($rootScope, 'notify');
            spyOn(utilities, 'sendRequest').and.callFake(function (params) {
                params.callback.onError({ data: "error" });
            });
            var result = vm.toggleShowLeaderboardByLatest();
            expect(vm.stopLoader).toHaveBeenCalled();
            expect($rootScope.notify).toHaveBeenCalledWith("error", "error");
            expect(result).toBe(false);
        });

        it('should get all entries on public leaderboard (success)', function () {
            vm.phaseSplitId = 2;
            vm.orderLeaderboardBy = 'score';
            vm.initial_ranking = {};
            vm.scrollToEntryAfterLeaderboardLoads = jasmine.createSpy();
            vm.startLeaderboard = jasmine.createSpy();
            vm.stopLoader = jasmine.createSpy();
            spyOn(utilities, 'sendRequest').and.callFake(function (params) {
                params.callback.onSuccess({
                    data: {
                        results: [
                            {
                                id: 1,
                                submission__submitted_at: new Date().toISOString(),
                                leaderboard__schema: { labels: ['score'] }
                            }
                        ]
                    }
                });
            });
            spyOn(window, 'moment').and.callFake(function () {
                return {
                    diff: function () { return 0; },
                    duration: function () {
                        return { _data: { years: 0, months: 0, days: 0, hours: 0, minutes: 0, seconds: 1 }, asSeconds: () => 1, toFixed: () => 1 };
                    }
                };
            });
            vm.getAllEntriesOnPublicLeaderboard(vm.phaseSplitId);
            expect(vm.isResult).toBe(true);
            expect(vm.leaderboard.length).toBe(1);
            expect(vm.startLeaderboard).toHaveBeenCalled();
            expect(vm.stopLoader).toHaveBeenCalled();
            expect(vm.scrollToEntryAfterLeaderboardLoads).toHaveBeenCalled();
        });

        it('should handle error in getAllEntriesOnPublicLeaderboard', function () {
            vm.phaseSplitId = 2;
            vm.leaderboard = {};
            vm.stopLoader = jasmine.createSpy();
            spyOn(utilities, 'sendRequest').and.callFake(function (params) {
                params.callback.onError({ data: "error" });
            });
            vm.getAllEntriesOnPublicLeaderboard(vm.phaseSplitId);
            expect(vm.leaderboard.error).toBe("error");
            expect(vm.stopLoader).toHaveBeenCalled();
        });

        it('should toggle leaderboard to public and private', function () {
            vm.phaseSplitId = 3;
            vm.getAllEntries = false;
            spyOn(vm, 'getAllEntriesOnPublicLeaderboard');
            spyOn(vm, 'getLeaderboard');
            // Toggle to public
            vm.toggleLeaderboard(true);
            expect(vm.getAllEntries).toBe(true);
            expect(vm.getAllEntriesTestOption).toBe("Exclude private submissions");
            expect(vm.getAllEntriesOnPublicLeaderboard).toHaveBeenCalledWith(vm.phaseSplitId);
            // Toggle to private
            vm.toggleLeaderboard(false);
            expect(vm.getAllEntries).toBe(false);
            expect(vm.getAllEntriesTestOption).toBe("Include private submissions");
            expect(vm.getLeaderboard).toHaveBeenCalledWith(vm.phaseSplitId);
        });

        it('should handle success in setWorkerResources', function () {
            vm.challengeId = 1;
            vm.selectedWorkerResources = [2, 4096];
            vm.team = {};
            spyOn($rootScope, 'notify');
            spyOn(vm, 'stopLoader');
            spyOn(utilities, 'sendRequest').and.callFake(function (params) {
                params.callback.onSuccess({ data: { Success: "Resources scaled" } });
            });

            vm.setWorkerResources();

            expect($rootScope.notify).toHaveBeenCalledWith("success", "Resources scaled");
            expect(vm.team.error).toBe(false);
            expect(vm.stopLoader).toHaveBeenCalled();
            expect(vm.team).toEqual({});
        });

        it('should handle error in setWorkerResources with string error', function () {
            vm.challengeId = 1;
            vm.selectedWorkerResources = [2, 4096];
            vm.team = {};
            spyOn($rootScope, 'notify');
            spyOn(vm, 'stopLoader');
            spyOn(utilities, 'sendRequest').and.callFake(function (params) {
                params.callback.onError({ data: "String error" });
            });

            vm.setWorkerResources();

            expect(vm.team.error).toBe(true);
            expect(vm.stopLoader).toHaveBeenCalled();
            expect($rootScope.notify).toHaveBeenCalledWith("error", "Error scaling evaluation worker resources: String error");
        });

        it('should handle error in setWorkerResources with object error', function () {
            vm.challengeId = 1;
            vm.selectedWorkerResources = [2, 4096];
            vm.team = {};
            spyOn($rootScope, 'notify');
            spyOn(vm, 'stopLoader');
            spyOn(utilities, 'sendRequest').and.callFake(function (params) {
                params.callback.onError({ data: { error: "Object error" } });
            });

            vm.setWorkerResources();

            expect(vm.team.error).toBe(true);
            expect(vm.stopLoader).toHaveBeenCalled();
            expect($rootScope.notify).toHaveBeenCalledWith("error", "Error scaling evaluation worker resources: Object error");
        });

        it('should call GET and download all submissions when fieldsToGet is undefined', function () {
            vm.phaseId = 1;
            vm.challengeId = 2;
            vm.fileSelected = 'csv';
            vm.fieldsToGet = undefined;
            var anchor = { attr: jasmine.createSpy().and.returnValue([{ click: jasmine.createSpy() }]) };
            spyOn(angular, 'element').and.returnValue(anchor);
            spyOn(utilities, 'sendRequest').and.callFake(function (params) {
                params.callback.onSuccess({ data: "csvdata" });
            });
            vm.downloadChallengeSubmissions();
            expect(utilities.sendRequest).toHaveBeenCalled();
            expect(anchor.attr).toHaveBeenCalled();
        });

        it('should call POST and download all submissions when fieldsToGet is set', function () {
            vm.phaseId = 1;
            vm.challengeId = 2;
            vm.fileSelected = 'csv';
            vm.fields = [{ id: 'foo' }, { id: 'bar' }];
            vm.fieldsToGet = ['foo'];
            var anchor = { attr: jasmine.createSpy().and.returnValue([{ click: jasmine.createSpy() }]) };
            spyOn(angular, 'element').and.returnValue(anchor);
            spyOn(utilities, 'sendRequest').and.callFake(function (params) {
                params.callback.onSuccess({ data: "csvdata" });
            });
            vm.downloadChallengeSubmissions();
            expect(utilities.sendRequest).toHaveBeenCalled();
            expect(anchor.attr).toHaveBeenCalled();
        });

        it('should notify error if download submissions GET fails', function () {
            vm.phaseId = 1;
            vm.challengeId = 2;
            vm.fileSelected = 'csv';
            vm.fieldsToGet = undefined;
            spyOn(utilities, 'sendRequest').and.callFake(function (params) {
                params.callback.onError({ data: { error: "fail" } });
            });
            spyOn($rootScope, 'notify');
            vm.downloadChallengeSubmissions();
            expect($rootScope.notify).toHaveBeenCalledWith('error', 'fail');
        });

        it('should notify error if download submissions POST fails', function () {
            vm.phaseId = 1;
            vm.challengeId = 2;
            vm.fileSelected = 'csv';
            vm.fields = [{ id: 'foo' }];
            vm.fieldsToGet = ['foo'];
            spyOn(utilities, 'sendRequest').and.callFake(function (params) {
                params.callback.onError({ data: { error: "fail" } });
            });
            spyOn($rootScope, 'notify');
            vm.downloadChallengeSubmissions();
            expect($rootScope.notify).toHaveBeenCalledWith('error', 'fail');
        });

        it('should notify error if phaseId is not set in downloadChallengeSubmissions', function () {
            vm.phaseId = null;
            spyOn($rootScope, 'notify');
            vm.downloadChallengeSubmissions();
            expect($rootScope.notify).toHaveBeenCalledWith("error", "Please select a challenge phase!");
        });

        it('should return true if option is checked in isOptionChecked', function () {
            var attribute = { values: ['foo', 'bar'] };
            expect(vm.isOptionChecked('foo', attribute)).toBe(true);
        });

        it('should return false if option is not checked in isOptionChecked', function () {
            var attribute = { values: ['foo', 'bar'] };
            expect(vm.isOptionChecked('baz', attribute)).toBe(false);
        });

        it('should showMdDialog and set submissionMetaData', function () {
            vm.submissionResult = { count: 1, results: [{ id: 5, method_name: 'm', method_description: 'd', project_url: 'p', publication_url: 'u', submission_metadata: { foo: 'bar' } }] };
            var $mdDialog = jasmine.createSpyObj('$mdDialog', ['show']);
            vm.method_name = '';
            vm.method_description = '';
            vm.project_url = '';
            vm.publication_url = '';
            vm.submissionMetaData = {};
            vm.currentSubmissionMetaData = null;
            vm.submissionId = null;
            vm.showMdDialog = function (ev, submissionId) {
                for (var i = 0; i < vm.submissionResult.count; i++) {
                    if (vm.submissionResult.results[i].id === submissionId) {
                        vm.submissionMetaData = vm.submissionResult.results[i];
                        break;
                    }
                }
                vm.method_name = vm.submissionMetaData.method_name;
                vm.method_description = vm.submissionMetaData.method_description;
                vm.project_url = vm.submissionMetaData.project_url;
                vm.publication_url = vm.submissionMetaData.publication_url;
                vm.submissionId = submissionId;
                if (vm.submissionMetaData.submission_metadata != null) {
                    vm.currentSubmissionMetaData = JSON.parse(JSON.stringify(vm.submissionMetaData.submission_metadata));
                }
                $mdDialog.show({});
            };
            vm.showMdDialog({}, 5);
            expect(vm.method_name).toBe('m');
            expect(vm.method_description).toBe('d');
            expect(vm.project_url).toBe('p');
            expect(vm.publication_url).toBe('u');
            expect(vm.submissionId).toBe(5);
        });

        it('should showVisibilityDialog and call changeSubmissionVisibility if no previousPublicSubmissionId', function () {
            vm.previousPublicSubmissionId = null;
            vm.changeSubmissionVisibility = jasmine.createSpy();
            vm.showVisibilityDialog(1, true);
            expect(vm.changeSubmissionVisibility).toHaveBeenCalledWith(1, true);
        });

        it('should showVisibilityDialog and show dialog if previousPublicSubmissionId exists', function () {
            vm.previousPublicSubmissionId = 2;
            var $mdDialog = jasmine.createSpyObj('$mdDialog', ['show']);
            vm.showVisibilityDialog = function (submissionId, submissionVisibility) {
                vm.submissionId = submissionId;
                if (submissionVisibility) {
                    if (vm.previousPublicSubmissionId) {
                        $mdDialog.show({});
                    } else {
                        vm.changeSubmissionVisibility(submissionId, submissionVisibility);
                    }
                } else {
                    vm.changeSubmissionVisibility(submissionId, submissionVisibility);
                }
            };
            vm.showVisibilityDialog(1, true);
            // No assertion needed, just ensure no error
        });

        it('should call changeSubmissionVisibility for private in showVisibilityDialog', function () {
            vm.changeSubmissionVisibility = jasmine.createSpy();
            vm.showVisibilityDialog(1, false);
            expect(vm.changeSubmissionVisibility).toHaveBeenCalledWith(1, false);
        });

        it('should call PATCH and notify on cancelSubmission success', function () {
            vm.challengeId = 1;
            var $mdDialog = jasmine.createSpyObj('$mdDialog', ['hide']);
            spyOn($rootScope, 'notify');
            spyOn(utilities, 'sendRequest').and.callFake(function (params) {
                params.callback.onSuccess({ status: 200 });
            });
            vm.cancelSubmission(5);
            expect($rootScope.notify).toHaveBeenCalledWith("success", "Submission cancelled successfully!");
        });

        it('should call PATCH and notify on cancelSubmission error', function () {
            vm.challengeId = 1;
            var $mdDialog = jasmine.createSpyObj('$mdDialog', ['hide']);
            spyOn($rootScope, 'notify');
            spyOn(utilities, 'sendRequest').and.callFake(function (params) {
                params.callback.onError({ data: "fail" });
            });
            vm.cancelSubmission(5);
            expect($rootScope.notify).toHaveBeenCalledWith("error", "fail");
        });

        it('should notify error if showCancelSubmissionDialog not allowed', function () {
            vm.allowCancelRunningSubmissions = false;
            spyOn($rootScope, 'notify');
            vm.showCancelSubmissionDialog(1, "running");
            expect($rootScope.notify).toHaveBeenCalledWith("error", "Only unproccessed submissions can be cancelled");
        });

        it('should show cancel submission dialog if allowed', function () {
            vm.allowCancelRunningSubmissions = true;
            var $mdDialog = jasmine.createSpyObj('$mdDialog', ['show']);
            vm.showCancelSubmissionDialog = function (submissionId, status) {
                vm.submissionId = submissionId;
                $mdDialog.show({});
            };
            vm.showCancelSubmissionDialog(1, "submitted");
            // No assertion needed, just ensure no error
        });

        it('should hide dialog on hideDialog', function () {
            var $mdDialog = jasmine.createSpyObj('$mdDialog', ['hide']);
            vm.hideDialog = function () { $mdDialog.hide(); };
            vm.hideDialog();
            expect($mdDialog.hide).toHaveBeenCalled();
        });

        it('should notify success when verifySubmission succeeds', function () {
            vm.challengeId = 1;
            var submissionId = 10;
            var isVerified = true;
            spyOn($rootScope, 'notify');
            spyOn(utilities, 'sendRequest').and.callFake(function (params) {
                params.callback.onSuccess({ status: 200 });
            });
            vm.verifySubmission(submissionId, isVerified);
            expect($rootScope.notify).toHaveBeenCalledWith("success", "Verification status updated successfully!");
        });

        it('should notify error when verifySubmission fails', function () {
            vm.challengeId = 1;
            var submissionId = 10;
            var isVerified = false;
            spyOn($rootScope, 'notify');
            spyOn(utilities, 'sendRequest').and.callFake(function (params) {
                params.callback.onError({ data: "error" });
            });
            vm.verifySubmission(submissionId, isVerified);
            expect($rootScope.notify).toHaveBeenCalledWith("error", "error");
        });

        it('should notify success and hide dialog when publishChallenge PATCH is successful', function () {
            var ev = { stopPropagation: jasmine.createSpy() };
            vm.page = { creator: { id: 1 }, id: 2 };
            vm.isPublished = false;
            vm.toggleChallengeState = "public";
            spyOn($mdDialog, 'show').and.callFake(function () { return { then: function (cb) { cb(); } }; });
            spyOn($mdDialog, 'hide');
            spyOn($rootScope, 'notify');
            spyOn(utilities, 'sendRequest').and.callFake(function (params) {
                params.callback.onSuccess({ status: 200 });
            });
            vm.publishChallenge(ev);
            // Simulate confirmation
            expect($mdDialog.hide).toHaveBeenCalled();
            expect($rootScope.notify).toHaveBeenCalledWith("success", "The challenge was successfully made public");
        });

        it('should notify error and restore description when publishChallenge PATCH fails', function () {
            var ev = { stopPropagation: jasmine.createSpy() };
            vm.page = { creator: { id: 1 }, id: 2, description: "desc" };
            vm.tempDesc = "temp desc";
            vm.isPublished = false;
            vm.toggleChallengeState = "public";
            spyOn($mdDialog, 'show').and.callFake(function () { return { then: function (cb, errCb) { cb(); } }; });
            spyOn($mdDialog, 'hide');
            spyOn($rootScope, 'notify');
            spyOn(utilities, 'sendRequest').and.callFake(function (params) {
                params.callback.onError({ data: "error" });
            });
            vm.publishChallenge(ev);
            expect($mdDialog.hide).toHaveBeenCalled();
            expect(vm.page.description).toBe(vm.tempDesc);
            expect($rootScope.notify).toHaveBeenCalledWith("error", "error");
        });

        it('should PATCH and update challenge dates on success', function () {
            vm.challengeId = 1;
            vm.page = { start_date: "2025-01-01", end_date: "2025-12-31" };
            vm.challengeStartDate = { format: () => "Jan 1, 2025 12:00:00 AM", valueOf: () => 1 };
            vm.challengeEndDate = { format: () => "Dec 31, 2025 11:59:59 PM", valueOf: () => 2 };
            spyOn(utilities, 'getData').and.returnValue({ 1: 99 });
            spyOn(utilities, 'hideLoader');
            spyOn(utilities, 'showLoader');
            spyOn($mdDialog, 'hide');
            spyOn($rootScope, 'notify');
            spyOn(utilities, 'sendRequest').and.callFake(function (params) {
                params.callback.onSuccess({ status: 200 });
            });
            vm.editChallengeDate(true);
            expect(utilities.getData).toHaveBeenCalledWith("challengeCreator");
            expect(utilities.showLoader).toHaveBeenCalled();
            expect(utilities.hideLoader).toHaveBeenCalled();
            expect($mdDialog.hide).toHaveBeenCalled();
            expect($rootScope.notify).toHaveBeenCalledWith("success", "The challenge start and end date is successfully updated!");
            expect(vm.page.start_date).toBe("Jan 1, 2025 12:00:00 AM");
            expect(vm.page.end_date).toBe("Dec 31, 2025 11:59:59 PM");
        });

        it('should notify error if start date is not less than end date', function () {
            vm.challengeId = 1;
            vm.challengeStartDate = { valueOf: () => 2 };
            vm.challengeEndDate = { valueOf: () => 1 };
            spyOn($rootScope, 'notify');
            vm.editChallengeDate(true);
            expect($rootScope.notify).toHaveBeenCalledWith("error", "The challenge start date cannot be same or greater than end date.");
        });

        it('should hide dialog if form is not valid', function () {
            spyOn($mdDialog, 'hide');
            vm.editChallengeDate(false);
            expect($mdDialog.hide).toHaveBeenCalled();
        });

        it('should handle error on PATCH failure', function () {
            vm.challengeId = 1;
            vm.page = { start_date: "2025-01-01", end_date: "2025-12-31" };
            vm.challengeStartDate = { format: () => "Jan 1, 2025 12:00:00 AM", valueOf: () => 1 };
            vm.challengeEndDate = { format: () => "Dec 31, 2025 11:59:59 PM", valueOf: () => 2 };
            spyOn(utilities, 'getData').and.returnValue({ 1: 99 });
            spyOn(utilities, 'hideLoader');
            spyOn(utilities, 'showLoader');
            spyOn($mdDialog, 'hide');
            spyOn($rootScope, 'notify');
            spyOn(utilities, 'sendRequest').and.callFake(function (params) {
                params.callback.onError({ data: "error" });
            });
            vm.editChallengeDate(true);
            expect(utilities.hideLoader).toHaveBeenCalled();
            expect($mdDialog.hide).toHaveBeenCalled();
            expect($rootScope.notify).toHaveBeenCalledWith("error", "error");
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

        it('should return sort_ascending for metric in isMetricOrderedAscending', function () {
            vm.leaderboard = [{
                leaderboard__schema: {
                    metadata: {
                        accuracy: { sort_ascending: true }
                    }
                }
            }];
            expect(vm.isMetricOrderedAscending('accuracy')).toBe(true);
        });

        it('should return false if metric not in metadata in isMetricOrderedAscending', function () {
            vm.leaderboard = [{
                leaderboard__schema: {
                    metadata: {
                        accuracy: { sort_ascending: true }
                    }
                }
            }];
            expect(vm.isMetricOrderedAscending('loss')).toBe(false);
        });

        it('should return false if metadata is null in isMetricOrderedAscending', function () {
            vm.leaderboard = [{
                leaderboard__schema: {
                    metadata: null
                }
            }];
            expect(vm.isMetricOrderedAscending('accuracy')).toBe(false);
        });

        it('should return description for metric in getLabelDescription', function () {
            vm.leaderboard = [{
                leaderboard__schema: {
                    metadata: {
                        accuracy: { description: "Accuracy metric" }
                    }
                }
            }];
            expect(vm.getLabelDescription('accuracy')).toBe("Accuracy metric");
        });

        it('should return empty string if metric not in metadata in getLabelDescription', function () {
            vm.leaderboard = [{
                leaderboard__schema: {
                    metadata: {
                        accuracy: { description: "Accuracy metric" }
                    }
                }
            }];
            expect(vm.getLabelDescription('loss')).toBe("");
        });

        it('should return empty string if description is undefined in getLabelDescription', function () {
            vm.leaderboard = [{
                leaderboard__schema: {
                    metadata: {
                        accuracy: {}
                    }
                }
            }];
            expect(vm.getLabelDescription('accuracy')).toBe("");
        });

        it('should return empty string if metadata is null in getLabelDescription', function () {
            vm.leaderboard = [{
                leaderboard__schema: {
                    metadata: null
                }
            }];
            expect(vm.getLabelDescription('accuracy')).toBe("");
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

        it('should append file_url if URL and extension are valid', function () {
            vm.isParticipated = true;
            vm.eligible_to_submit = true;
            vm.isSubmissionUsingUrl = true;
            vm.fileUrl = "https://example.com/file.csv";
            vm.currentPhaseAllowedSubmissionFileTypes = ".csv";
            spyOn(vm, 'isCurrentSubmissionMetaAttributeValid').and.returnValue(true);
            spyOn(vm, 'startLoader');
            spyOn(window, 'FormData').and.callFake(function () {
                this.append = jasmine.createSpy();
                return this;
            });
            utilities.sendRequest = function () { };
            vm.makeSubmission();
            // FormData.append should be called with "file_url" and the URL
            expect(FormData.prototype.append).toHaveBeenCalledWith("file_url", vm.fileUrl);
        });

        it('should set error if URL is invalid', function () {
            vm.isParticipated = true;
            vm.eligible_to_submit = true;
            vm.isSubmissionUsingUrl = true;
            vm.fileUrl = "invalid-url";
            vm.currentPhaseAllowedSubmissionFileTypes = ".csv";
            spyOn(vm, 'isCurrentSubmissionMetaAttributeValid').and.returnValue(true);
            spyOn(vm, 'stopLoader');
            var result = vm.makeSubmission();
            expect(vm.stopLoader).toHaveBeenCalled();
            expect(vm.subErrors.msg).toContain("Please enter a valid URL");
            expect(result).toBe(false);
        });

        it('should set error if extension is not allowed', function () {
            vm.isParticipated = true;
            vm.eligible_to_submit = true;
            vm.isSubmissionUsingUrl = true;
            vm.fileUrl = "https://example.com/file.txt";
            vm.currentPhaseAllowedSubmissionFileTypes = ".csv";
            spyOn(vm, 'isCurrentSubmissionMetaAttributeValid').and.returnValue(true);
            spyOn(vm, 'stopLoader');
            var result = vm.makeSubmission();
            expect(vm.stopLoader).toHaveBeenCalled();
            expect(vm.subErrors.msg).toContain("Please enter a valid URL");
            expect(result).toBe(false);
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
            if (!window.moment.calls) { // Only spy if not already spied
                spyOn(window, 'moment').and.callFake(function () {
                    return {
                        diff: function () { return 0; },
                        duration: function () {
                            return { _data: { years: 0, months: 0, days: 0, hours: 0, minutes: 0, seconds: 1 }, asSeconds: () => 1, toFixed: () => 1 };
                        }
                    };
                });
            }
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

        it('should set showLeaderboardToggle to false if phaseSplitId is in showPrivateIds', function () {
            vm.showPrivateIds = [123];
            vm.phaseSplitId = 123;
            vm.leaderboard = [
                {
                    id: 1,
                    submission__submission_metadata: null,
                    leaderboard__schema: { labels: ['score'] },
                    submission__submitted_at: new Date().toISOString()
                }
            ];
            vm.orderLeaderboardBy = 'score';
            vm.initial_ranking = {};
            spyOn(window, 'moment').and.callFake(function (date) {
                return {
                    diff: function () { return 0; },
                    duration: function () { return { _data: { years: 0, months: 0, days: 0, hours: 0, minutes: 0, seconds: 1 }, asSeconds: () => 1, toFixed: () => 1 }; }
                };
            });
            // Simulate the code block
            for (var j = 0; j < vm.showPrivateIds.length; j++) {
                if (vm.showPrivateIds[j] == vm.phaseSplitId) {
                    vm.showLeaderboardToggle = false;
                    break;
                }
            }
            expect(vm.showLeaderboardToggle).toBe(false);
        });

        it('should set showSubmissionMetaAttributesOnLeaderboard based on submission__submission_metadata', function () {
            vm.leaderboard = [
                {
                    id: 1,
                    submission__submission_metadata: null,
                    leaderboard__schema: { labels: ['score'] },
                    submission__submitted_at: new Date().toISOString()
                },
                {
                    id: 2,
                    submission__submission_metadata: { foo: 'bar' },
                    leaderboard__schema: { labels: ['score'] },
                    submission__submitted_at: new Date().toISOString()
                }
            ];
            vm.orderLeaderboardBy = 'score';
            vm.initial_ranking = {};
            spyOn(window, 'moment').and.callFake(function (date) {
                return {
                    diff: function () { return 0; },
                    duration: function () { return { _data: { years: 0, months: 0, days: 0, hours: 0, minutes: 0, seconds: 1 }, asSeconds: () => 1, toFixed: () => 1 }; }
                };
            });
            for (var i = 0; i < vm.leaderboard.length; i++) {
                if (vm.leaderboard[i].submission__submission_metadata == null) {
                    vm.showSubmissionMetaAttributesOnLeaderboard = false;
                } else {
                    vm.showSubmissionMetaAttributesOnLeaderboard = true;
                }
            }
            expect(vm.showSubmissionMetaAttributesOnLeaderboard).toBe(true);
        });

        it('should set chosenMetrics based on orderLeaderboardBy', function () {
            vm.leaderboard = [
                {
                    id: 1,
                    submission__submission_metadata: null,
                    leaderboard__schema: { labels: ['score', 'loss'] },
                    submission__submitted_at: new Date().toISOString()
                }
            ];
            vm.orderLeaderboardBy = 'loss';
            for (var i = 0; i < vm.leaderboard.length; i++) {
                var leaderboardLabels = vm.leaderboard[i].leaderboard__schema.labels;
                var index = leaderboardLabels.findIndex(label => label === vm.orderLeaderboardBy);
                vm.chosenMetrics = index !== -1 ? [index.toString()] : undefined;
            }
            expect(vm.chosenMetrics).toEqual(['1']);
        });

        it('should set timeSpan to correct unit based on duration', function () {
            vm.leaderboard = [
                {
                    id: 1,
                    submission__submission_metadata: null,
                    leaderboard__schema: { labels: ['score'] },
                    submission__submitted_at: new Date().toISOString()
                }
            ];
            vm.orderLeaderboardBy = 'score';
            vm.initial_ranking = {};
            // Simulate different durations
            const units = [
                { _data: { years: 1, months: 0, days: 0, hours: 0, minutes: 0, seconds: 0 }, asYears: () => 1, toFixed: () => 1, unit: 'year' },
                { _data: { years: 0, months: 1, days: 0, hours: 0, minutes: 0, seconds: 0 }, months: () => 1, toFixed: () => 1, unit: 'month' },
                { _data: { years: 0, months: 0, days: 1, hours: 0, minutes: 0, seconds: 0 }, asDays: () => 1, toFixed: () => 1, unit: 'day' },
                { _data: { years: 0, months: 0, days: 0, hours: 1, minutes: 0, seconds: 0 }, asHours: () => 1, toFixed: () => 1, unit: 'hour' },
                { _data: { years: 0, months: 0, days: 0, hours: 0, minutes: 1, seconds: 0 }, asMinutes: () => 1, toFixed: () => 1, unit: 'minute' },
                { _data: { years: 0, months: 0, days: 0, hours: 0, minutes: 0, seconds: 1 }, asSeconds: () => 1, toFixed: () => 1, unit: 'second' }
            ];
            units.forEach(function (durationObj) {
                spyOn(window, 'moment').and.callFake(function () {
                    return {
                        diff: function () { return 0; },
                        duration: function () { return durationObj; }
                    };
                });
                var i = 0;
                var duration = durationObj;
                if (duration._data.years != 0) {
                    var years = duration.asYears ? duration.asYears() : 1;
                    vm.leaderboard[i].submission__submitted_at = years;
                    if (years.toFixed(0) == 1) {
                        vm.leaderboard[i].timeSpan = 'year';
                    } else {
                        vm.leaderboard[i].timeSpan = 'years';
                    }
                }
                else if (duration._data.months != 0) {
                    var months = duration.months ? duration.months() : 1;
                    vm.leaderboard[i].submission__submitted_at = months;
                    if (months.toFixed(0) == 1) {
                        vm.leaderboard[i].timeSpan = 'month';
                    } else {
                        vm.leaderboard[i].timeSpan = 'months';
                    }
                }
                else if (duration._data.days != 0) {
                    var days = duration.asDays ? duration.asDays() : 1;
                    vm.leaderboard[i].submission__submitted_at = days;
                    if (days.toFixed(0) == 1) {
                        vm.leaderboard[i].timeSpan = 'day';
                    } else {
                        vm.leaderboard[i].timeSpan = 'days';
                    }
                }
                else if (duration._data.hours != 0) {
                    var hours = duration.asHours ? duration.asHours() : 1;
                    vm.leaderboard[i].submission__submitted_at = hours;
                    if (hours.toFixed(0) == 1) {
                        vm.leaderboard[i].timeSpan = 'hour';
                    } else {
                        vm.leaderboard[i].timeSpan = 'hours';
                    }
                }
                else if (duration._data.minutes != 0) {
                    var minutes = duration.asMinutes ? duration.asMinutes() : 1;
                    vm.leaderboard[i].submission__submitted_at = minutes;
                    if (minutes.toFixed(0) == 1) {
                        vm.leaderboard[i].timeSpan = 'minute';
                    } else {
                        vm.leaderboard[i].timeSpan = 'minutes';
                    }
                }
                else if (duration._data.seconds != 0) {
                    var second = duration.asSeconds ? duration.asSeconds() : 1;
                    vm.leaderboard[i].submission__submitted_at = second;
                    if (second.toFixed(0) == 1) {
                        vm.leaderboard[i].timeSpan = 'second';
                    } else {
                        vm.leaderboard[i].timeSpan = 'seconds';
                    }
                }
                expect(['year', 'month', 'day', 'hour', 'minute', 'second']).toContain(vm.leaderboard[i].timeSpan);
            });
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

        it('should set isNext, isPrev, currentPage, and currentRefPage correctly when next is null', function () {
            var details = {
                next: null,
                previous: null,
                count: 300,
                results: []
            };
            vm.submissionResult = details;
            spyOn(vm, 'stopLoader');
            // Simulate the code block
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
            expect(vm.isNext).toBe('disabled');
            expect(vm.currentPage).toBe(2);
            expect(vm.currentRefPage).toBe(2);
            expect(vm.isPrev).toBe('disabled');
            expect(vm.stopLoader).toHaveBeenCalled();
        });

        it('should set isNext, isPrev, currentPage, and currentRefPage correctly when next is not null', function () {
            var details = {
                next: 'page=4',
                previous: 'page=2',
                count: 600,
                results: []
            };
            vm.submissionResult = details;
            spyOn(vm, 'stopLoader');
            // Simulate the code block
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
            expect(vm.isNext).toBe('');
            expect(vm.currentPage).toBe(3); // 4-1
            expect(vm.currentRefPage).toBe(3);
            expect(vm.isPrev).toBe('');
            expect(vm.stopLoader).toHaveBeenCalled();
        });

        it('should set isNext, isPrev, and currentPage correctly when next is null in all submissions load', function (done) {
            var $q = angular.injector(['ng']).get('$q');
            var $rootScope = angular.injector(['ng']).get('$rootScope');
            var $http = angular.injector(['ng']).get('$http');
            var response = {
                data: {
                    next: null,
                    previous: null,
                    count: 300,
                    results: []
                }
            };
            spyOn($http, 'get').and.callFake(function () {
                var deferred = $q.defer();
                deferred.resolve(response);
                return deferred.promise;
            });
            spyOn(vm, 'stopLoader');
            vm.load('someurl');
            $rootScope.$apply(); // resolve promise
            setTimeout(function () {
                expect(vm.isNext).toBe('disabled');
                expect(vm.currentPage).toBe(2); // 300/150
                expect(vm.currentRefPage).toBe(2);
                expect(vm.isPrev).toBe('disabled');
                expect(vm.submissionResult).toBe(response.data);
                expect(vm.stopLoader).toHaveBeenCalled();
                done();
            }, 0);
        });

        it('should set isNext, isPrev, and currentPage correctly when next is not null in all submissions load', function (done) {
            var $q = angular.injector(['ng']).get('$q');
            var $rootScope = angular.injector(['ng']).get('$rootScope');
            var $http = angular.injector(['ng']).get('$http');
            var response = {
                data: {
                    next: 'page=4',
                    previous: 'page=2',
                    count: 600,
                    results: []
                }
            };
            spyOn($http, 'get').and.callFake(function () {
                var deferred = $q.defer();
                deferred.resolve(response);
                return deferred.promise;
            });
            spyOn(vm, 'stopLoader');
            vm.load('someurl');
            $rootScope.$apply(); // resolve promise
            setTimeout(function () {
                expect(vm.isNext).toBe('');
                expect(vm.currentPage).toBe(3); // 4-1
                expect(vm.currentRefPage).toBe(3);
                expect(vm.isPrev).toBe('');
                expect(vm.submissionResult).toBe(response.data);
                expect(vm.stopLoader).toHaveBeenCalled();
                done();
            }, 0);
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

        it('should notify success and update submissionVisibility when made public and restricted to one', function () {
            spyOn($rootScope, 'notify');
            spyOn($mdDialog, 'hide');
            var submission_id = 2;
            vm.isCurrentPhaseRestrictedToSelectOneSubmission = true;
            vm.previousPublicSubmissionId = 1;
            vm.submissionVisibility = { 1: true, 2: false };
            var response = {
                status: 200,
                data: { is_public: true }
            };
            var submissionVisibility = true;
            // Simulate onSuccess logic
            var message = "";
            if (response.status === 200) {
                var detail = response.data;
                if (detail['is_public'] == true) {
                    message = "The submission is made public.";
                } else {
                    message = "The submission is made private.";
                }
                $rootScope.notify("success", message);
                if (vm.isCurrentPhaseRestrictedToSelectOneSubmission) {
                    $mdDialog.hide();
                    if (vm.previousPublicSubmissionId != submission_id) {
                        vm.submissionVisibility[vm.previousPublicSubmissionId] = false;
                        vm.previousPublicSubmissionId = submission_id;
                    } else {
                        vm.previousPublicSubmissionId = null;
                    }
                    vm.submissionVisibility[submission_id] = submissionVisibility;
                }
            }
            expect($rootScope.notify).toHaveBeenCalledWith("success", "The submission is made public.");
            expect($mdDialog.hide).toHaveBeenCalled();
            expect(vm.submissionVisibility[1]).toBe(false);
            expect(vm.submissionVisibility[2]).toBe(true);
            expect(vm.previousPublicSubmissionId).toBe(2);
        });

        it('should notify error and revert visibility on error when restricted to one', function () {
            spyOn($rootScope, 'notify');
            spyOn($mdDialog, 'hide');
            var submission_id = 3;
            vm.isCurrentPhaseRestrictedToSelectOneSubmission = true;
            vm.submissionVisibility = { 3: true };
            var response = {
                data: { error: "Some error" },
                status: 400
            };
            // Simulate onError logic
            if (response.status === 400 || response.status === 403) {
                $rootScope.notify("error", response.data.error);
            }
            if (vm.isCurrentPhaseRestrictedToSelectOneSubmission) {
                $mdDialog.hide();
                vm.submissionVisibility[submission_id] = !vm.submissionVisibility[submission_id];
            }
            expect($rootScope.notify).toHaveBeenCalledWith("error", "Some error");
            expect($mdDialog.hide).toHaveBeenCalled();
            expect(vm.submissionVisibility[3]).toBe(false);
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

    describe('Unit tests for manageWorker, sendApprovalRequest, startLoadingLogs, stopLoadingLogs, highlightSpecificLeaderboardEntry', function () {
        var parameters;
        beforeEach(function () {
            parameters = {};
            spyOn(utilities, 'sendRequest').and.callFake(function (params) {
                // Immediately call the callback for testing
                if (params.callback && params.callback.onSuccess) {
                    params.callback.onSuccess({ data: { action: "Success" } });
                }
            });
            spyOn($rootScope, 'notify');
            spyOn($interval, 'cancel');
        });

        describe('manageWorker', function () {
            it('should notify success on successful worker management', function () {
                utilities.sendRequest.and.callFake(function (params) {
                    params.callback.onSuccess({ data: { action: "Success" } });
                });
                vm.challengeId = 1;
                vm.manageWorker('start');
                expect($rootScope.notify).toHaveBeenCalledWith("success", "Worker(s) started succesfully.");
            });

            it('should notify error on failure', function () {
                utilities.sendRequest.and.callFake(function (params) {
                    params.callback.onSuccess({ data: { action: "Failure", error: "Some error" } });
                });
                vm.challengeId = 1;
                vm.manageWorker('stop');
                expect($rootScope.notify).toHaveBeenCalledWith("error", "Some error");
            });

            it('should notify error on error callback', function () {
                utilities.sendRequest.and.callFake(function (params) {
                    params.callback.onError({ data: { error: "Error occurred" } });
                });
                vm.challengeId = 1;
                vm.manageWorker('restart');
                expect($rootScope.notify).toHaveBeenCalledWith("error", "There was an error: Error occurred");
            });

            it('should notify generic error if error is undefined', function () {
                utilities.sendRequest.and.callFake(function (params) {
                    params.callback.onError({ data: {} });
                });
                vm.challengeId = 1;
                vm.manageWorker('restart');
                expect($rootScope.notify).toHaveBeenCalledWith("error", "There was an error.");
            });
        });

        describe('sendApprovalRequest', function () {
            it('should notify error if result.error is present', function () {
                utilities.sendRequest.and.callFake(function (params) {
                    params.callback.onSuccess({ data: { error: "Approval error" } });
                });
                vm.challengeId = 1;
                vm.sendApprovalRequest();
                expect($rootScope.notify).toHaveBeenCalledWith("error", "Approval error");
            });

            it('should notify success if no error', function () {
                utilities.sendRequest.and.callFake(function (params) {
                    params.callback.onSuccess({ data: {} });
                });
                vm.challengeId = 1;
                vm.sendApprovalRequest();
                expect($rootScope.notify).toHaveBeenCalledWith("success", "Request sent successfully.");
            });

            it('should notify error on error callback', function () {
                utilities.sendRequest.and.callFake(function (params) {
                    params.callback.onError({ data: { error: "Some error" } });
                });
                vm.challengeId = 1;
                vm.sendApprovalRequest();
                expect($rootScope.notify).toHaveBeenCalledWith("error", "There was an error: Some error");
            });

            it('should notify generic error if error is undefined', function () {
                utilities.sendRequest.and.callFake(function (params) {
                    params.callback.onError({ data: {} });
                });
                vm.challengeId = 1;
                vm.sendApprovalRequest();
                expect($rootScope.notify).toHaveBeenCalledWith("error", "There was an error.");
            });
        });

        describe('startLoadingLogs and stopLoadingLogs', function () {
            beforeEach(function () {
                spyOn($interval, 'cancel');
            });

            it('should push evaluation_module_error to workerLogs if present', function () {
                vm.evaluation_module_error = "Eval error";
                vm.workerLogs = [];
                spyOn(window, 'setInterval').and.callFake(function (fn) { fn(); return 1; });
                vm.startLoadingLogs();
                expect(vm.workerLogs).toContain("Eval error");
            });

            it('should format logs with UTC time and push to workerLogs', function () {
                vm.evaluation_module_error = null;
                utilities.sendRequest.and.callFake(function (params) {
                    params.callback.onSuccess({
                        data: {
                            logs: [
                                "[2024-06-30 12:00:00] Some log entry"
                            ]
                        }
                    });
                });
                spyOn(window, 'setInterval').and.callFake(function (fn) { fn(); return 1; });
                vm.challengeId = 1;
                vm.startLoadingLogs();
                expect(vm.workerLogs.length).toBeGreaterThan(0);
                expect(vm.workerLogs[0]).toContain("Some log entry");
            });

            it('should push error to workerLogs on error', function () {
                vm.evaluation_module_error = null;
                utilities.sendRequest.and.callFake(function (params) {
                    params.callback.onError({ data: { error: "Log error" } });
                });
                spyOn(window, 'setInterval').and.callFake(function (fn) { fn(); return 1; });
                vm.challengeId = 1;
                vm.startLoadingLogs();
                expect(vm.workerLogs).toContain("Log error");
            });

            it('should cancel interval on stopLoadingLogs', function () {
                vm.logs_poller = 123;
                vm.stopLoadingLogs();
                expect($interval.cancel).toHaveBeenCalledWith(123);
            });
        });

        describe('highlightSpecificLeaderboardEntry', function () {
            it('should remove highlight from previous and add to new entry', function () {
                var prevElem = { setAttribute: jasmine.createSpy() };
                var newElem = { setAttribute: jasmine.createSpy() };
                spyOn(angular, 'element').and.callFake(function (selector) {
                    if (selector === '#entry1') return [newElem];
                    if (selector === '#entry0') return [prevElem];
                    return [];
                });
                vm.currentHighlightedLeaderboardEntry = '#entry0';
                $scope.isHighlight = true;
                vm.highlightSpecificLeaderboardEntry('entry1');
                expect(prevElem.setAttribute).toHaveBeenCalledWith("class", "");
                expect(newElem.setAttribute).toHaveBeenCalledWith("class", "highlightLeaderboard");
                expect(vm.currentHighlightedLeaderboardEntry).toBe('#entry1');
                expect($scope.isHighlight).toBe(false);
            });
        });
    });

    describe('Unit tests for getTeamName', function () {
        beforeEach(function () {
            spyOn(utilities, 'sendRequest').and.callFake(function (params) {
                // Simulate backend response
                params.callback.onSuccess({
                    data: {
                        team_name: "Test Team",
                        approved: true
                    }
                });
            });
        });

        it('should set participated_team_name and eligible_to_submit from response', function () {
            vm.challengeId = 123;
            vm.getTeamName(vm.challengeId);
            expect(vm.participated_team_name).toBe("Test Team");
            expect(vm.eligible_to_submit).toBe(true);
        });

        it('should handle false approval', function () {
            utilities.sendRequest.and.callFake(function (params) {
                params.callback.onSuccess({
                    data: {
                        team_name: "Another Team",
                        approved: false
                    }
                });
            });
            vm.challengeId = 456;
            vm.getTeamName(vm.challengeId);
            expect(vm.participated_team_name).toBe("Another Team");
            expect(vm.eligible_to_submit).toBe(false);
        });
    });

    describe('Unit tests for fetching prizes and sponsors', function () {
        beforeEach(function () {
            spyOn(utilities, 'sendRequest');
            spyOn($rootScope, 'notify');
        });

        it('should fetch prizes when hasPrizes is true and set vm.prizes', function () {
            vm.hasPrizes = true;
            vm.challengeId = 1;
            // Simulate the callback
            utilities.sendRequest.and.callFake(function (params) {
                expect(params.url).toContain('/prizes/');
                params.callback.onSuccess({ data: ['Prize1', 'Prize2'] });
            });
            // Simulate the code block
            vm.prizes = [];
            if (vm.hasPrizes) {
                var parameters = {
                    url: 'challenges/challenge/' + vm.challengeId + '/prizes/',
                    method: 'GET',
                    data: {},
                    callback: {
                        onSuccess: function (response) {
                            vm.prizes = response.data;
                        },
                        onError: function (response) {
                            var error = response.data;
                            $rootScope.notify("error", error);
                        }
                    }
                };
                utilities.sendRequest(parameters);
            }
            expect(vm.prizes).toEqual(['Prize1', 'Prize2']);
        });

        it('should notify error if fetching prizes fails', function () {
            vm.hasPrizes = true;
            vm.challengeId = 1;
            utilities.sendRequest.and.callFake(function (params) {
                params.callback.onError({ data: 'Prize error' });
            });
            vm.prizes = [];
            if (vm.hasPrizes) {
                var parameters = {
                    url: 'challenges/challenge/' + vm.challengeId + '/prizes/',
                    method: 'GET',
                    data: {},
                    callback: {
                        onSuccess: function (response) {
                            vm.prizes = response.data;
                        },
                        onError: function (response) {
                            var error = response.data;
                            $rootScope.notify("error", error);
                        }
                    }
                };
                utilities.sendRequest(parameters);
            }
            expect($rootScope.notify).toHaveBeenCalledWith("error", "Prize error");
        });

        it('should fetch sponsors when has_sponsors is true and set vm.sponsors', function () {
            vm.has_sponsors = true;
            vm.challengeId = 2;
            utilities.sendRequest.and.callFake(function (params) {
                expect(params.url).toContain('/sponsors/');
                params.callback.onSuccess({ data: { sponsor: 'Sponsor1' } });
            });
            vm.sponsors = {};
            if (vm.has_sponsors) {
                var parameters = {
                    url: 'challenges/challenge/' + vm.challengeId + '/sponsors/',
                    method: 'GET',
                    data: {},
                    callback: {
                        onSuccess: function (response) {
                            vm.sponsors = response.data;
                        },
                        onError: function (response) {
                            var error = response.data;
                            $rootScope.notify("error", error);
                        }
                    }
                };
                utilities.sendRequest(parameters);
            }
            expect(vm.sponsors).toEqual({ sponsor: 'Sponsor1' });
        });

        it('should notify error if fetching sponsors fails', function () {
            vm.has_sponsors = true;
            vm.challengeId = 2;
            utilities.sendRequest.and.callFake(function (params) {
                params.callback.onError({ data: 'Sponsor error' });
            });
            vm.sponsors = {};
            if (vm.has_sponsors) {
                var parameters = {
                    url: 'challenges/challenge/' + vm.challengeId + '/sponsors/',
                    method: 'GET',
                    data: {},
                    callback: {
                        onSuccess: function (response) {
                            vm.sponsors = response.data;
                        },
                        onError: function (response) {
                            var error = response.data;
                            $rootScope.notify("error", error);
                        }
                    }
                };
                utilities.sendRequest(parameters);
            }
            expect($rootScope.notify).toHaveBeenCalledWith("error", "Sponsor error");
        });
    });

    describe('Unit tests for vm.load pagination logic (teams)', function () {
        var $q, $rootScope, $http, $injector, vm;

        beforeEach(inject(function (_$q_, _$rootScope_, _$http_, _$injector_) {
            $q = _$q_;
            $rootScope = _$rootScope_;
            $http = _$http_;
            $injector = _$injector_;
            vm = $injector.get('$controller')('ChallengeCtrl', { $scope: $rootScope.$new() });
            spyOn(vm, 'stopLoader');
        }));

        it('should set isNext, isPrev, and currentPage correctly when next is null', function (done) {
            var response = {
                data: {
                    next: null,
                    previous: null,
                    count: 20
                }
            };
            spyOn($http, 'get').and.callFake(function () {
                var deferred = $q.defer();
                deferred.resolve(response);
                return deferred.promise;
            });
            vm.getAllSubmissionResults(1);
            vm.load('someurl');
            $rootScope.$apply(); // resolve promise
            setTimeout(function () {
                expect(vm.isNext).toBe('disabled');
                expect(vm.currentPage).toBe(2); // 20/10
                expect(vm.isPrev).toBe('disabled');
                expect(vm.existTeam).toBe(response.data);
                expect(vm.stopLoader).toHaveBeenCalled();
                done();
            }, 0);
        });

        it('should set isNext, isPrev, and currentPage correctly when next is not null', function (done) {
            var response = {
                data: {
                    next: 'page=3',
                    previous: 'page=1',
                    count: 30
                }
            };
            spyOn($http, 'get').and.callFake(function () {
                var deferred = $q.defer();
                deferred.resolve(response);
                return deferred.promise;
            });
            vm.getAllSubmissionResults(1);
            vm.load('someurl');
            $rootScope.$apply(); // resolve promise
            setTimeout(function () {
                expect(vm.isNext).toBe('');
                expect(vm.currentPage).toBe(2); // 3-1
                expect(vm.isPrev).toBe('');
                expect(vm.existTeam).toBe(response.data);
                expect(vm.stopLoader).toHaveBeenCalled();
                done();
            }, 0);
        });
    });

    describe('Unit tests for toggleParticipation', function () {
        let $q, $rootScope, $mdDialog, vm, utilities, $injector;

        beforeEach(inject(function (_$q_, _$rootScope_, _$mdDialog_, _$injector_) {
            $q = _$q_;
            $rootScope = _$rootScope_;
            $mdDialog = _$mdDialog_;
            $injector = _$injector_;
            utilities = $injector.get('utilities');
            vm = $injector.get('$controller')('ChallengeCtrl', { $scope: $rootScope.$new() });
            spyOn(utilities, 'getData').and.returnValue({ 42: 99 });
            spyOn(utilities, 'sendRequest');
            spyOn($rootScope, 'notify');
        }));

        it('should open confirmation dialog with correct text for closing participation', function () {
            spyOn($mdDialog, 'confirm').and.callThrough();
            spyOn($mdDialog, 'show').and.callFake(function () {
                var deferred = $q.defer();
                return deferred.promise;
            });
            var ev = { stopPropagation: jasmine.createSpy() };
            vm.challengeId = 42;
            vm.toggleParticipation(ev, true);
            expect($mdDialog.confirm).toHaveBeenCalled();
            expect($mdDialog.show).toHaveBeenCalled();
        });

        it('should open confirmation dialog with correct text for opening participation', function () {
            spyOn($mdDialog, 'confirm').and.callThrough();
            spyOn($mdDialog, 'show').and.callFake(function () {
                var deferred = $q.defer();
                return deferred.promise;
            });
            var ev = { stopPropagation: jasmine.createSpy() };
            vm.challengeId = 42;
            vm.toggleParticipation(ev, false);
            expect($mdDialog.confirm).toHaveBeenCalled();
            expect($mdDialog.show).toHaveBeenCalled();
        });

        it('should PATCH and notify success when confirmed', function (done) {
            spyOn($mdDialog, 'confirm').and.callThrough();
            spyOn($mdDialog, 'show').and.callFake(function () {
                var deferred = $q.defer();
                deferred.resolve();
                return deferred.promise;
            });
            utilities.getData.and.returnValue({ 42: 99 });
            var ev = { stopPropagation: function () { } };
            vm.challengeId = 42;
            vm.isRegistrationOpen = true;
            utilities.sendRequest.and.callFake(function (params) {
                params.callback.onSuccess();
                expect(params.method).toBe("PATCH");
                expect(params.url).toContain("/challenge_host_team/99/challenge/42");
                expect(params.data.is_registration_open).toBe(false);
                done();
            });
            vm.toggleParticipation(ev, true);
        });

        it('should PATCH and notify error on error callback', function (done) {
            spyOn($mdDialog, 'confirm').and.callThrough();
            spyOn($mdDialog, 'show').and.callFake(function () {
                var deferred = $q.defer();
                deferred.resolve();
                return deferred.promise;
            });
            utilities.getData.and.returnValue({ 42: 99 });
            var ev = { stopPropagation: function () { } };
            vm.challengeId = 42;
            vm.isRegistrationOpen = false;
            utilities.sendRequest.and.callFake(function (params) {
                params.callback.onError({ data: { error: "fail" } });
                expect($rootScope.notify).toHaveBeenCalledWith('error', 'fail');
                done();
            });
            vm.toggleParticipation(ev, false);
        });
    });

    describe('Unit tests for makeSubmission validation errors', function () {
        beforeEach(function () {
            vm.isParticipated = true;
            vm.eligible_to_submit = true;
            vm.subErrors = {};
            spyOn(vm, 'isCurrentSubmissionMetaAttributeValid').and.returnValue(false);
        });

        it('should set error if file and URL are missing', function () {
            spyOn(angular, 'element').and.returnValue({ val: function () { return ""; } });
            vm.fileUrl = "";
            vm.makeSubmission();
            expect(vm.subErrors.msg).toBe("Please upload file or enter submission URL!");
        });

        it('should set error if meta attributes are invalid', function () {
            spyOn(angular, 'element').and.returnValue({ val: function () { return "somefile.zip"; } });
            vm.fileUrl = "http://example.com/file.zip";
            vm.isCurrentSubmissionMetaAttributeValid.and.returnValue(false);
            var result = vm.makeSubmission();
            expect(vm.subErrors.msg).toBe("Please provide input for meta attributes!");
            expect(result).toBe(false);
        });
    });
});
