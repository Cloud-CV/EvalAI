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
            controllerAs: 'main',
            title: "Welcome"
        }

        var auth = {
            name: "auth",
            url: "/auth",
            templateUrl: baseUrl + "/web/auth.html",
            controller: 'AuthCtrl',
            controllerAs: 'auth',
            abstract: true,
            authenticate: false,
            title: 'Auth'
        }

        var login = {
            name: "auth.login",
            parent: "auth",
            url: "/login",
            templateUrl: baseUrl + "/web/login.html",
            authenticate: false,
            title: 'Login'
        }

        var signup = {
            name: "auth.signup",
            parent: "auth",
            url: "/signup",
            templateUrl: baseUrl + "/web/signup.html",
            authenticate: false,
            title: 'SignUp'
        }

        var logout = {
            name: "auth.logout",
            parent: "auth",
            url: "/logout",
            authenticate: false,
            title: 'Logout'
        }

        // main app 'web'
        var web = {
            name: "web",
            url: "/web",
            templateUrl: baseUrl + "/web/web.html",
            controller: 'WebCtrl',
            controllerAs: 'web',
            authenticate: true,
            abstract: true
        }

        var dashboard = {
            name: "web.dashboard",
            parent: "web",
            url: "/dashboard",
            templateUrl: baseUrl + "/web/dashboard.html",
            controller: 'DashCtrl',
            controllerAs: 'dash',
            title: 'Dashboard',
            authenticate: true
        }

        var profile = {
            name: "web.profile",
            parent: "web",
            url: "/profile",
            templateUrl: baseUrl + "/web/profile.html",
            title: "Profile",
            controller: 'ProfileCtrl',
            controllerAs: 'profile',
            authenticate: true
        }


        // call all states here
        $stateProvider.state(home);

        // auth configs
        $stateProvider.state(auth);
        $stateProvider.state(login);
        $stateProvider.state(signup);
        $stateProvider.state(logout);

        // web main configs.
        $stateProvider.state(web);
        $stateProvider.state(dashboard);
        $stateProvider.state(profile);

        $urlRouterProvider.otherwise("/");

    }

})();

// define run block here
(function() {

    angular
        .module('evalai')
        .run(runFunc);

    function runFunc($rootScope, $state, utilities, $window) {
        $rootScope.isAuth = false;
        // check for valid user
        $rootScope.$on('$stateChangeStart', function(event, toState, toParams, fromState, fromParams) {
            if (toState.authenticate && !utilities.isAuthenticated()) {
                $rootScope.isAuth = false;
                // User isn’t authenticated
                $state.transitionTo("auth.login");
                event.preventDefault();
            }
            // restrict authorized user too access login/signup page
            else if (toState.authenticate == false && utilities.isAuthenticated()) {
                // alert("")
                $rootScope.isAuth = true;
                $state.transitionTo("home");
                event.preventDefault();
                return false;
            } else if (utilities.isAuthenticated()) {
                $rootScope.isAuth = true;
            }
        });

        $rootScope.$on('$stateChangeSuccess', function(event, toState, toParams, fromState, fromParams) {
            // Save the route title
            $rootScope.pageTitle = $state.current.title;
            // alert($rootScope.pageTitle)

        });

        $rootScope.logout = function() {
            var userKey = utilities.getData('userKey');
            var parameters = {};
            parameters.url = 'auth/logout/';
            parameters.method = 'POST';
            parameters.token = userKey;
            parameters.callback = {
                onSuccess: function(response, status) {
                    utilities.resetStorage();
                    $state.go("home");
                    $rootScope.isAuth=false;
                },
                onError: function() {

                }
            };

            utilities.sendRequest(parameters);
        }
    };
})();
