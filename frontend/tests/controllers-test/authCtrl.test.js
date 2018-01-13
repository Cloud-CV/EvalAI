'use strict';

describe('Test for auth controller', function() {
    beforeEach(angular.mock.module('evalai'));

    var $controller, $rootScope, $state, $window, $scope, utilities, vm;

    var notifyType, notifyMessage;

	beforeEach(inject(function(_$controller_, _$rootScope_, _$state_, _utilities_) {
		$controller = _$controller_;
		$rootScope = _$rootScope_;
		$state = _$state_;
		utilities = _utilities_;

		$rootScope.notify = function(type, message) {
			notifyType = type;
			notifyMessage = message;
		}

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

	describe('userSignUp', function() {
		beforeEach(function() {
			vm.regUser = {
				name: 'Ford Prefect',
				email: 'fordprefect@hitchhikers.guide',
				password: 'dontpanic',
				confirm_password: 'dontpanic'
			};

			utilities.sendRequest = function(parameters) {
				if(typeof(parameters.data.username) !== 'string' ||
				  typeof(parameters.data.email) !== 'string' ||
				  typeof(parameters.data.password1) !== 'string' ||
				  parameters.data.password1 !== parameters.data.password2) {
					var data = {};

					if(typeof(parameters.data.username) !== 'string')
						data.username = ['username error'];
					else if(typeof(parameters.data.email) !== 'string')
						data.email = ['email error'];
					else if(typeof(parameters.data.password1) !== 'string')
						data.password1 = ['password error'];
					else if(parameters.data.password1 !== parameters.data.password2)
						data.password2 = ['password confirm error'];

					parameters.callback.onError({
						status: 400,
						data: data
					})
				}
				else {
					parameters.callback.onSuccess({
						status: 201
					});
				}
			}
		});

		it('correct sign up details', function() {
			vm.userSignUp(true);
			expect(notifyType).to.equal('success');
		});

		it('missing username', function() {
			delete vm.regUser.name;
			vm.userSignUp(true);
			expect(vm.FormError).to.equal('username error');
		});

		it('missing email', function() {
			delete vm.regUser.email;
			vm.userSignUp(true);
			expect(vm.FormError).to.equal('email error');
		});

		it('missing password', function() {
			delete vm.regUser.password;
			vm.userSignUp(true);
			expect(vm.FormError).to.equal('password error');
		});

		it('mismatch password', function() {
			vm.regUser.confirm_password = 'failword';
			vm.userSignUp(true);
			expect(vm.FormError).to.equal('password confirm error');
		});
	});
});
