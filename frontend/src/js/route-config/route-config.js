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

		var auth = {
			name: "auth",
			url:"/auth",
			templateUrl: baseUrl + "/web/auth.html",
			controller: 'AuthCtrl',
			controllerAs : 'auth',
			abstract: true
		}

		var login = {
			name: "auth.login",
			parent: "auth",
			url:"/login",
			templateUrl: baseUrl + "/web/login.html",
		}

		var signup = {
			name: "auth.signup",
			parent: "auth",
			url:"/signup",
			templateUrl: baseUrl + "/web/signup.html",
		}

		var dashboard = {
			name: "dashboard",
			url:"/dashboard",
			templateUrl: baseUrl + "/web/dashboard.html",
			controller: 'DashCtrl',
			controllerAs : 'dash',
		}

		// call all states here
		$stateProvider.state(home);

		// auth configs
		$stateProvider.state(auth);
		$stateProvider.state(login);
		$stateProvider.state(signup);

		// dashboard
		$stateProvider.state(dashboard);

		$urlRouterProvider.otherwise("/");

	}

})();
