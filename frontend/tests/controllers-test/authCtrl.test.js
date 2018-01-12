'use strict';

describe('Test for auth controller', function() {
    beforeEach(angular.mock.module('evalai'));

    var $controller, $rootScope, $window, $scope, vm;

	beforeEach(inject(function(_$controller_, _$rootScope_) {
		$controller = _$controller_;
		$rootScope = _$rootScope_;

		$scope = $rootScope.$new();
		vm = $controller('AuthCtrl', { $scope: $scope });
	}));

	it('startLoader', function() {
		vm.startLoader('loading tests');

		expect($rootScope.isLoader).to.equal(true);
		expect($rootScope.loaderTitle).to.equal('loading tests');
	});

	it('stopLoader', function() {
		vm.stopLoader();

		expect($rootScope.isLoader).to.equal(false);
		expect($rootScope.loaderTitle).to.equal('');
	});

	it('resetForm', function() {
		vm.resetForm();

		expect(vm.regUser).to.be.empty;
		expect(vm.getUser).to.be.empty;
		expect(vm.wrnMsg).to.be.empty;
		expect(vm.isFormError).to.equal(false);
		expect(vm.isMail).to.equal(true);
	});
});
