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
	.config(['$httpProvider',function ($httpProvider) {
		$httpProvider.interceptors.push('preventTemplateCache');
	}])
	.config(['$compileProvider', function($compileProvider) {
		$compileProvider.aHrefSanitizationWhitelist(/^\s*(https?|file|tel|javascript):/);
	}]);
