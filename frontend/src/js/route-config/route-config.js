/**
 * Config for the router
 */

(function() {
    angular
        .module('evalai')
        .config(configure);

    var baseUrl = "dist/views/"

    function configure($stateProvider, $urlRouterProvider, $locationProvider) {

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
            controllerAs: 'main'
        }

        var auth = {
            name: "auth",
            url: "/auth",
            templateUrl: baseUrl + "/web/auth.html",
            controller: 'AuthCtrl',
            controllerAs: 'auth',
            abstract: true,
            authenticate: false
        }

        var login = {
            name: "auth.login",
            parent: "auth",
            url: "/login",
            templateUrl: baseUrl + "/web/login.html",
            authenticate: false
        }

        var signup = {
            name: "auth.signup",
            parent: "auth",
            url: "/signup",
            templateUrl: baseUrl + "/web/signup.html",
            authenticate: false
        }

        var dashboard = {
            name: "dashboard",
            url: "/dashboard",
            templateUrl: baseUrl + "/web/dashboard.html",
            controller: 'DashCtrl',
            controllerAs: 'dash',
            authenticate: true
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

// define run block here
(function() {

    angular
        .module('evalai')
        .run(runFunc);

    function runFunc($rootScope, $state, utilities, $window) {

    	// check for valid user
        $rootScope.$on('$stateChangeStart', function(event, toState, toParams, fromState, fromParams) {
        	if (toState.authenticate && !utilities.isAuthenticated()){
			  // User isn’t authenticated
			  $state.transitionTo("auth.login");
			  event.preventDefault(); 
			}
        });

        // global function for logout
        $rootScope.onLogout = function() {
            utilities.deleteData('userKey');
            utilities.storeData('isRem', false)
            $state.go('home');
        };
    }

})();
