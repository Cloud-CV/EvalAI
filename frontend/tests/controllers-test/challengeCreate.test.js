'use strict';

describe('Unit tests for challenge create controller', function() {
	beforeEach(angular.mock.module('evalai'));

	var $controller, $rootScope, $state, $scope, loaderService, utilities, vm;

	beforeEach(inject(function(_$controller_, _$rootScope_, _$state_, _utilities_, _loaderService_) {
        $controller = _$controller_;
        $rootScope = _$rootScope_;
        $state = _$state_;
        utilities = _utilities_;
        loaderService = _loaderService_;
        
        $scope = $rootScope.$new();
        vm = $controller('ChallengeCreateCtrl', { $scope: $scope });
    }));

    describe('Global variables', function() {
        it('has default values', function() {
            expect(vm.wrnMsg).toEqual({});
            expect(vm.isValid).toEqual({});
            expect(vm.isFormError).toEqual(false);
            expect(vm.isSyntaxErrorInYamlFile).toEqual(false);
            expect(vm.input_file).toEqual(null);
            expect(vm.formError).toEqual({});
            expect(vm.syntaxErrorInYamlFile).toEqual({});
            expect(vm.isExistLoader).toEqual(false);
            expect(vm.loaderTitle).toEqual('');
            expect(vm.startLoader).toEqual(loaderService.startLoader);
            expect(vm.stopLoader).toEqual(loaderService.stopLoader);
        });
    });

    describe('Unit tests for challengeCreate function', function() {
    	var success;

    	beforeEach(function() {
            utilities.sendRequest = function(parameters) {
                if (success) {
                    parameters.callback.onSuccess({
                    	status: 201,
                    	data: 'success'
                    });
                } else {
                    parameters.callback.onError({
                    	data: {
                    		error: 'error',
                    	}
                    });
                }
            };
        });

    	it('when host team not selected `vm.hostTeamId=null`', function() {
    		vm.challengeCreate();
    		expect(vm.infoMsg).toEqual("Please select a challenge host team!");
    	});

    	it('success of `challenges/challenge/challenge_host_team/<host_team_id>/zip_upload/`', function() {
    		success = true;
    		vm.hostTeamId = 1;
    		vm.input_file = 'challenge_conf.zip'
    		spyOn($state, 'go');
    		vm.challengeCreate();
    		expect(vm.isExistLoader).toEqual(true);
    		expect(vm.loaderTitle).toEqual('create challenge');
    		expect($state.go).toHaveBeenCalledWith('home');
    	});

    	it('error of `challenges/challenge/challenge_host_team/<host_team_id>/zip_upload/`', function() {
    		success = false;
    		vm.hostTeamId = 1;
    		vm.input_file = 'challenge_conf.zip'
    		vm.challengeCreate();
    		expect(vm.isSyntaxErrorInYamlFile).toEqual(true);
    		expect(vm.syntaxErrorInYamlFile).toEqual('error');
    		expect(vm.isExistLoader).toEqual(false);
    	});
    });
});
