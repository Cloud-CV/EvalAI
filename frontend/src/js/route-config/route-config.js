
/**
 * Config for the router
 */

 (function(){
 	angular
	.module('evalai')
	.config(configure);

	var baseUrl = "dist/views/"

	function configure ($stateProvider, $urlRouterProvider, $locationProvider){

			// formating hashed url
		$locationProvider.html5Mode({
			enabled: true,
			requireBase: true
		});

		

		// declare all states parameters here
		var home = {
			name: "home",
			url: "/",
	        templateUrl: baseUrl + "/web/landing.html",
	        controller: 'MainCtrl',
	        controllerAs : 'main'
		}

		var login = {
			name: "login",
			url:"/login",
	    	templateUrl: baseUrl + "/web/login.html",
	    	controller: 'AuthCtrl',
	        controllerAs : 'auth'
		}



		// call all states here

	    $stateProvider.state(home);
	    $stateProvider.state(login);

	    $urlRouterProvider.otherwise("/");

	}

 })();


		
