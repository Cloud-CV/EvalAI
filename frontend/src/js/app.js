// declare app and related dependencies here
angular
	.module('evalai', [
		'ui.router',
		'ngMaterial',
		'ngAnimate',
		'ngMessages',
		'evalai-config',
		'smoothScroll',
		'focus-if',
		'ngSanitize',
		'ngFileUpload',
		'toaster',
		'angularTrix',
		'angularMoment',
		'ngclipboard',
		'moment-picker'
	])
	.service('preventTemplateCache', [function() {
		var service = this;
		service.request = function(config) {
			var urlSegments = config.url.split('/');
			// Check each segment for "/dist/"
			var isDistUrl = urlSegments.some(function(segment) {
				return segment === 'dist';
			});
			if (isDistUrl) {
				config.url = config.url + '?t=___REPLACE_IN_GULP___';

			}
			return config;
		};
	}])
	.factory('authFailureInterceptor', [
		'$injector',
		'$q',
		function($injector, $q) {
			return {
				responseError: function(response) {
					if (response.status === 401) {
						var $state = $injector.get('$state');
						var $rootScope = $injector.get('$rootScope');
						var utilities = $injector.get('utilities');
						utilities.resetStorage();
						$rootScope.isAuth = false;
						$state.go('auth.login');
						alert('Timeout, Please login again to continue!');
					}
					return $q.reject(response);
				}
			};
		}
	])
	.config(['$httpProvider', function($httpProvider) {
		$httpProvider.interceptors.push('preventTemplateCache');
		$httpProvider.interceptors.push('authFailureInterceptor');
	}])
	.config(['$compileProvider', function($compileProvider) {
		$compileProvider.aHrefSanitizationWhitelist(/^\s*(https?|file|tel|javascript):/);
	}]);
