'use strict';

describe('Unit tests for analytics controller', function() {
	beforeEach(angular.mock.module('evalai'));

	var $controller, createController, $rootScope, $state, $scope, utilities, vm, userKey;

	beforeEach(inject(function(_$controller_, _$rootScope_, _$state_, _utilities_) {
		$controller = _$controller_;
        $rootScope = _$rootScope_;
        utilities = _utilities_;
        $state = _$state_;

        $scope = $rootScope.$new();
        createController = function () {
        	return $controller('AnalyticsCtrl', { $scope: $scope });
        };
        vm = $controller('AnalyticsCtrl', { $scope: $scope });
	}));

	describe('Global Variables', function() {
		it('has default values', function() {
			expect(vm.hostTeam).toEqual({});
			expect(vm.teamId).toEqual(null);
			expect(vm.currentTeamName).toEqual(null);
			expect(vm.challengeListCount).toEqual(0);
			expect(vm.challengeList).toEqual({});
			expect(vm.challengeAnalysisDetail).toEqual({});
			expect(vm.isTeamSelected).toEqual(false);
			expect(vm.challengeId).toEqual(null);
			expect(vm.currentChallengeDetails).toEqual({});
			expect(vm.currentPhase).toEqual([]);
			expect(vm.totalSubmission).toEqual({});
			expect(vm.totalParticipatedTeams).toEqual({});
			expect(vm.lastSubmissionTime).toEqual({});

			utilities.storeData('userKey', 'encrypted');
			userKey = utilities.getData('userKey');
		})
	});

	describe('Unit tests for global backend call `hosts/challenge_host_team/`', function () {
		var success;
		var success_response = {
			results: {
				team_name: "Team name",
				team_url: "Team url",
				created_by: "user"
			}
		};
		var error_response = 'error';

		beforeEach(function() {
			spyOn($state, 'go');
			spyOn(window, 'alert');
			spyOn(utilities, 'resetStorage');

            utilities.sendRequest = function(parameters) {
                if (success) {
                    parameters.callback.onSuccess({
                    	data: success_response,
                    	status: 200
                    });
                } else {
                    parameters.callback.onError({
                    	data: error_response,
                    	status: status
                    });
                }
            };
        });

		it('get the host team details', function () {
			success = true;
			vm = createController();
			expect(vm.hostTeam).toEqual(success_response.results);
		});

		it('403 backend error', function () {
			success = false;
			status = 403;
			vm = createController();
			expect(vm.error).toEqual(error_response);
			expect($state.go).toHaveBeenCalledWith('web.permission-denied');
		});

		it('401 backend error', function () {
			success = false;
			status = 401;
			vm = createController();
			expect(window.alert).toHaveBeenCalledWith("Timeout, Please login again to continue!");
			expect(utilities.resetStorage).toHaveBeenCalled();
			expect($state.go).toHaveBeenCalledWith('auth.login');
			expect($rootScope.isAuth).toBeFalsy();
		});
	});

	describe('Unit tests for total challenges hosted `challenges/challenge?mode=host`', function() {
		beforeEach(function() {
			utilities.sendRequest = function(parameters) {
				var data, status;
				var success = 'success';
				var error = 'error';

				if (parameters.token != userKey) {
					data = error;
					status = 403;
				}
				else {
					data = success;
					status = 200;
				}

				return {
					'data': data,
					'status': status
				}
			};
		});

		it('successfully listed the hosted challenges', function() {
			var parameters = {
				token: userKey
			}
			var response = utilities.sendRequest(parameters);
			expect(response.status).toEqual(200);
			expect(response.data).toEqual('success');
		});

		it('permission denied page', function() {
			var parameters = {
				token: 'nullKey'
			}
			var response = utilities.sendRequest(parameters);
			expect(response.status).toEqual(403);
			expect(response.data).toEqual('error');
		});
	});

	describe('Unit tests for `showChallengeAnalysis` function', function() {
		var phaseDetailsSuccess, currentPhaseDetailsSuccess, teamsCountSuccess;
		var successResponse, participantTeamCount = 10;
		var status;

		beforeEach(function() {
			spyOn(window, 'alert');
			spyOn(utilities, 'resetStorage');
			spyOn($state, 'go');

            utilities.sendRequest = function(parameters) {
				if ((phaseDetailsSuccess && parameters.url === 'challenges/challenge/2/challenge_phase') ||
				(teamsCountSuccess && parameters.url === 'analytics/challenge/2/team/count') ||
				(currentPhaseDetailsSuccess && parameters.url === 'analytics/challenge/2/challenge_phase/4/analytics')) {
					parameters.callback.onSuccess({
						status: 200,
						data: successResponse
					});
                } else {
					parameters.callback.onError({
						status: status,
						data: 'error'
					});
                }
            };
		});

		it('when challenge Id is null', function() {
			phaseDetailsSuccess = null;
			teamsCountSuccess = null;
			currentPhaseDetailsSuccess = null;
			vm.challengeId = null;
			vm.showChallengeAnalysis();
			expect(vm.isTeamSelected).toEqual(false);
		});
		
		it('on success `challenges/challenge/<challenge_id>/challenge_phase`', function() {
			phaseDetailsSuccess = true;
			teamsCountSuccess = null;
			currentPhaseDetailsSuccess = null;
			vm.challengeId = 2;
			successResponse = {
				'participant_team_count': participantTeamCount,
				'results': {
					id: 4,
					name: "test-dev",
					description: "this is test-dev description"
				}
			}
			vm.showChallengeAnalysis();
			expect(vm.isTeamSelected).toEqual(true);
		});

		it('backend error with status 403 `challenges/challenge/<challenge_id>/challenge_phase`', function() {
			phaseDetailsSuccess = false;
			teamsCountSuccess = null;
			currentPhaseDetailsSuccess = null;
			status = 403;
			vm.challengeId = 2;
			successResponse = {
				'participant_team_count': participantTeamCount,
				'results': {
					id: 4,
					name: "test-dev",
					description: "this is test-dev description"
				}
			}
			vm.showChallengeAnalysis();
			expect(vm.error).toEqual('error');
		});

		it('backend error with status 401 `challenges/challenge/<challenge_id>/challenge_phase`', function() {
			phaseDetailsSuccess = false;
			teamsCountSuccess = null;
			currentPhaseDetailsSuccess = null;
			status = 401;
			vm.challengeId = 2;
			successResponse = {
				'participant_team_count': participantTeamCount,
				'results': {
					id: 4,
					name: "test-dev",
					description: "this is test-dev description"
				}
			}
			vm.showChallengeAnalysis();
			expect(window.alert).toHaveBeenCalledWith('Timeout, Please login again to continue!');
			expect(utilities.resetStorage).toHaveBeenCalled();
			expect($state.go).toHaveBeenCalledWith('auth.login');
			expect($rootScope.isAuth).toBeFalsy();
		});

		it('on success `analytics/challenge/<challenge_id>/team/count`', function() {
			phaseDetailsSuccess = true;
			teamsCountSuccess = true;
			currentPhaseDetailsSuccess = null;
			vm.challengeId = 2;
			successResponse = {
				'participant_team_count': participantTeamCount,
				'results': {
					id: 4,
					name: "test-dev",
					description: "this is test-dev description"
				}
			}
			vm.showChallengeAnalysis();
			expect(vm.isTeamSelected).toEqual(true);
			expect(vm.totalChallengeTeams).toEqual(participantTeamCount);
		});

		it('backend error with status 403 `analytics/challenge/<challenge_id>/team/count`', function() {
			phaseDetailsSuccess = true;
			teamsCountSuccess = false;
			currentPhaseDetailsSuccess = null;
			status = 403;
			vm.challengeId = 2;
			successResponse = {
				'participant_team_count': participantTeamCount,
				'results': {
					id: 4,
					name: "test-dev",
					description: "this is test-dev description"
				}
			}
			vm.showChallengeAnalysis();
			expect(vm.error).toEqual('error');
		});

		it('backend error with status 401 `analytics/challenge/<challenge_id>/team/count`', function() {
			phaseDetailsSuccess = true;
			teamsCountSuccess = false;
			currentPhaseDetailsSuccess = null;
			status = 401;
			vm.challengeId = 2;
			successResponse = {
				'participant_team_count': participantTeamCount,
				'results': {
					id: 4,
					name: "test-dev",
					description: "this is test-dev description"
				}
			}
			vm.showChallengeAnalysis();
			expect(window.alert).toHaveBeenCalledWith('Timeout, Please login again to continue!');
			expect(utilities.resetStorage).toHaveBeenCalled();
			expect($state.go).toHaveBeenCalledWith('auth.login');
			expect($rootScope.isAuth).toBeFalsy();
		});

		it('backend error `analytics/challenge/<challenge_id>/challenge_phase/<current_phase_id>/analytics`',
		function() {
			phaseDetailsSuccess = true;
			teamsCountSuccess = true;
			currentPhaseDetailsSuccess = false;
			status = 401;
			vm.challengeId = 2;
			successResponse = {
				'participant_team_count': participantTeamCount,
				'results': [
					{
						id: 4,
						name: "test-dev",
						description: "this is test-dev description"
					}
				]
			}
			vm.showChallengeAnalysis();
			expect(vm.currentPhase).toEqual(successResponse.results);
			expect(window.alert).toHaveBeenCalledWith('Timeout, Please login again to continue!');
			expect(utilities.resetStorage).toHaveBeenCalled();
			expect($state.go).toHaveBeenCalledWith('auth.login');
			expect($rootScope.isAuth).toBeFalsy();
		});
	});
});
