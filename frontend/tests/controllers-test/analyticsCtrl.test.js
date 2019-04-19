'use strict';

describe('Unit Tests for analytics controller', function() {
	beforeEach(angular.mock.module('evalai'));

	var $controller, $rootScope, $scope, utilities, vm, userKey;

	beforeEach(inject(function(_$controller_, _$rootScope_, _utilities_) {
		$controller = _$controller_;
        $rootScope = _$rootScope_;
        utilities = _utilities_;

        $scope = $rootScope.$new();
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

	describe('Unit Tets for Total Chllenges Hosted', function() {
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

		it('permission denied page', function() {
			var parameters = {
				token: 'nullKey'
			}
			var response = utilities.sendRequest(parameters);
			expect(response.status).toEqual(403);
			expect(response.data).toEqual('error');
		});

		it('successfully listed the hosted challenges', function() {
			var parameters = {
				token: userKey
			}
			var response = utilities.sendRequest(parameters);
			expect(response.status).toEqual(200);
			expect(response.data).toEqual('success');
		});
	});

	describe('Unit Tests for Showing Challenge Analysis', function() {
		var success, participant_team_count = 10;

		beforeEach(function() {
            utilities.sendRequest = function(parameters) {
                if (success) {
                    parameters.callback.onSuccess({
                    	status: 200,
                    	data: {
                    		participant_team_count: participant_team_count,
                    		results: {
                    			id: 4,
                    			name: "test-dev",
                    			description: "this is test-dev description"
                    		}
                    	}
                    });
                } else {
                    parameters.callback.onError({
                    	status: 403,
                    	data: 'error',
                    });
                }
            };
        });

        it('null challengeId', function() {
        	success = false;
        	vm.showChallengeAnalysis();
        	expect(vm.challengeId).toEqual(null);
        	expect(vm.isTeamSelected).toEqual(false);
        });

		it('backend error', function() {
			success = false;
			vm.challengeId = 2;
			vm.showChallengeAnalysis();
			expect(vm.isTeamSelected).toEqual(true);
			expect(vm.error).toEqual('error');
		});

		it('on success', function() {
			success = true;
			vm.showChallengeAnalysis();
			vm.challengeId = 2;
			vm.showChallengeAnalysis();
			expect(vm.isTeamSelected).toEqual(true);
			expect(vm.totalChallengeTeams).toEqual(participant_team_count);
		});
	});
});
