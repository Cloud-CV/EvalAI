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
	]).config(['$compileProvider', function($compileProvider) {
    $compileProvider.aHrefSanitizationWhitelist(/^\s*(https?|file|tel|javascript):/);
}]);
