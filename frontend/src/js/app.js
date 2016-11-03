// decalre all apps and config scripts here

var app = angular.module('evalai', ['ui.router']);


// config scripts


/**
 * Config for the router
 */
app.config(['$stateProvider', '$urlRouterProvider', '$locationProvider', function ($stateProvider, $urlRouterProvider, $locationProvider){


	// formating hashed url
	$locationProvider.html5Mode({
		enabled: true,
		requireBase: false
	});

	$urlRouterProvider.otherwise("/");

	 // Set up the states
    $stateProvider.state('home', {
        url: "/",
        templateUrl: "dist/assets/views/landing.html"
    });

}])