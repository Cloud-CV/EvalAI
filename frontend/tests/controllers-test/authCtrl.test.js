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

	describe('general form functions', function() {
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

	describe('userSignUp', function() {
		var errors = {
			username: 'username error',
			email: 'email error',
			password1: 'password error',
			password2: 'password confirme error'
		};

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
						data.username = [errors.username];
					else if(typeof(parameters.data.email) !== 'string')
						data.email = [errors.email];
					else if(typeof(parameters.data.password1) !== 'string')
						data.password1 = [errors.password1];
					else if(parameters.data.password1 !== parameters.data.password2)
						data.password2 = [errors.password2];

					parameters.callback.onError({
						status: 400,
						data: data
					});
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
			expect(vm.FormError).to.equal(errors.username);
		});

		it('missing email', function() {
			delete vm.regUser.email;
			vm.userSignUp(true);
			expect(vm.FormError).to.equal(errors.email);
		});

		it('missing password', function() {
			delete vm.regUser.password;
			vm.userSignUp(true);
			expect(vm.FormError).to.equal(errors.password1);
		});

		it('mismatch password', function() {
			vm.regUser.confirm_password = 'failword';
			vm.userSignUp(true);
			expect(vm.FormError).to.equal(errors.password2);
		});

		it('invalid details', function() {
			vm.userSignUp(false);
			expect($rootScope.isLoader).to.equal(false);
		});
	});

	describe('userLogin', function() {
		var nonFieldErrors, token;

		beforeEach(function() {
			nonFieldErrors = false;

			vm.getUser = {
				name: 'fordprefect',
				password: 'dontpanic',
			};

			utilities.sendRequest = function(parameters) {
				if(nonFieldErrors) {
					var data = {};
					data.non_field_errors = ['backend error'];

					parameters.callback.onError({
						status: 400,
						data: data
					});
				}
				else {
					token = {
						value: 'secure'
					};
					parameters.callback.onSuccess({
						status: 200,
						data: {
							token: token
						}
					});
				}
			};
		});

		it('correct sign in details', function() {
			vm.userLogin(true);
			var savedData = utilities.getData('userKey');
			expect(angular.equals(savedData, token)).to.equal(true);
		});

		it('backend error', function() {
			nonFieldErrors = true;
			vm.userLogin(true);
			expect(vm.FormError).to.equal('backend error')
		});

		it('invalid details', function() {
			vm.userLogin(false);
			expect($rootScope.isLoader).to.equal(false);
		});
	});

	describe('verifyEmail', function() {
		var verified;

		beforeEach(function() {
			utilities.sendRequest = function(parameters) {
				if(verified) {
					parameters.callback.onSuccess();
				}
				else {
					parameters.callback.onError();
				}
			};
		});

		it('correct email', function() {
			verified = true;
			vm.verifyEmail();
			expect(vm.email_verify_msg).to.equal('Your email has been verified successfully');
		});

		it('incorrect email', function() {
			verified = false;
			vm.verifyEmail();
			expect(vm.email_verify_msg).to.equal('Something went wrong!! Please try again.');
		});
	});

	describe('resetPassword', function() {
		var success;

		var mailSent = 'mail sent';

		beforeEach(function() {
			utilities.sendRequest = function(parameters) {
				if(success) {
					parameters.callback.onSuccess({
						data: {
							success: mailSent
						}
					});
				}
				else {
					parameters.callback.onError();
				}
			};
		});

		it('sent successfully', function() {
			success = true;
			vm.resetPassword(true);
			expect(vm.isFormError).to.equal(false);
			expect(vm.deliveredMsg).to.equal(mailSent);
		});

		it('backend error', function() {
			success = false;
			vm.resetPassword(true);
			expect(vm.isFormError).to.equal(true);
		});

		it('invalid details', function() {
			vm.resetPassword(false);
			expect($rootScope.isLoader).to.equal(false);
		});
	});

	describe('resetPasswordConfirm', function() {
		var success;

		var resetConfirm = 'password reset confirmed';

		beforeEach(function() {
			utilities.sendRequest = function(parameters) {
				if(success) {
					parameters.callback.onSuccess({
						data: {
							detail: resetConfirm
						}
					});
				}
				else {
					parameters.callback.onError();
				}
			};
		});

		it('successful reset', function() {
			$state.params.user_id = 42;
			$state.params.reset_token = 'secure';
			success = true;
			vm.resetPasswordConfirm(true);
			expect(vm.isResetPassword).to.equal(true);
			expect(vm.deliveredMsg).to.equal(resetConfirm);
		});

		it('backend error', function() {
			$state.params.user_id = 42;
			success = false;
			vm.resetPasswordConfirm(true);
			expect(vm.isFormError).to.equal(true);
		});

		it('invalid details', function() {
			vm.resetPasswordConfirm(false);
			expect($rootScope.isLoader).to.equal(false);
		});
	});
});
