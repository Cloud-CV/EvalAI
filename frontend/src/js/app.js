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
		'ngclipboard'
<<<<<<< HEAD
	]);
=======
	]).config(['$compileProvider', function($compileProvider) {
    $compileProvider.aHrefSanitizationWhitelist(/^\s*(https?|file|tel|javascript):/);
}]);
>>>>>>> 98065e3257db0cd629bc64b959a29bae519b0bfe
