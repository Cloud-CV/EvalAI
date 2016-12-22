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

        var reset_password = {
            name: "auth.reset-password",
            parent: "auth",
            url: "/reset-password",
            templateUrl: baseUrl + "/web/reset-password.html",
            title: "Reset Password",
            controller: 'ResetPwdCtrl',
            controllerAs: 'resetpwd',
            authenticate: false,
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

        var teams = {
            name: "web.teams",
            parent: "web",
            url: "/teams",
            templateUrl: baseUrl + "/web/teams.html",
            controller: 'TeamsCtrl',
            controllerAs: 'teams',
            title: 'Teams',
            authenticate: true
        }

        var challenge_page = {
            name: "web.challenge-page",
            parent: "web",
            url: "/challenge-page",
            templateUrl: baseUrl + "/web/challenge-page.html",
            controller: 'ChallengeCtrl',
            controllerAs: 'challenge',
            redirectTo: "web.challenge-page.overview",
            authenticate: true
        }

        var overview = {
            name: "web.challenge-page.overview",
            parent: "web.challenge-page",
            url: "/overview",
            templateUrl: baseUrl + "/web/challenge/overview.html",
            title: 'Overview',
            authenticate: true
        }

        var evaluation = {
            name: "web.challenge-page.evaluation",
            url: "/evaluation",
            templateUrl: baseUrl + "/web/challenge/evaluation.html",
            title: 'Evaluation',
            authenticate: true
        }

        var phases = {
            name: "web.challenge-page.phases",
            url: "/phases",
            templateUrl: baseUrl + "/web/challenge/phases.html",
            title: 'Phases',
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

        var host_challenge = {
            name: "web.host-challenge",
            parent: "web",
            url: "/host-challenge",
            templateUrl: baseUrl + "/web/host-challenge.html",
            title: 'Host Competition',
            // controller: 'HostCtrl',
            // controllerAs: 'host',
            authenticate: true
        }

        var permission_denied = {
            name: "web.permission-denied",
            parent: "web",
            url: "/permission-denied",
            templateUrl: baseUrl + "/web/permission-denied.html",
            title: "Permission Denied",
            controller: 'PermCtrl',
            controllerAs: 'perm',
            authenticate: true
        }

        var change_password = {
            name: "web.change-password",
            parent: "web",
            url: "/change-password",
            templateUrl: baseUrl + "/web/change-password.html",
            title: "Change Password",
            controller: 'ChangePwdCtrl',
            controllerAs: 'changepwd',
            authenticate: true
        }


        // call all states here
        $stateProvider.state(home);

        // auth configs
        $stateProvider.state(auth);
        $stateProvider.state(login);
        $stateProvider.state(signup);
        $stateProvider.state(reset_password);
        $stateProvider.state(logout);

        // web main configs.
        $stateProvider.state(web);
        $stateProvider.state(dashboard);
        $stateProvider.state(teams);

        $stateProvider.state(challenge_page);
        $stateProvider.state(overview);
        $stateProvider.state(evaluation);
        $stateProvider.state(phases);

        $stateProvider.state(host_challenge);


        $stateProvider.state(profile);
        $stateProvider.state(permission_denied);
        $stateProvider.state(change_password);

        $urlRouterProvider.otherwise("/");

    }

})();

// define run block here
(function() {

    angular
        .module('evalai')
        .run(runFunc);

    function runFunc($rootScope, $state, utilities, $window) {

        // setting timout for token (7days)
        // var getTokenTime = utilities.getData('tokenTime');
        // var timeNow = (new Date()).getTime();
        // .getTime() returns milliseconds, so for 7 days 1000 * 60 * 60 * 24 * 7 = 7 days
        // var tokenExpTime = 1000 * 60 * 60 * 24 * 7;
        // if ((timeNow - getTokenTime) > tokenExpTime) {
        //     utilities.resetStorage();
        // }

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

        $rootScope.$on('$stateChangeStart', function(event, to, params) {
            if (to.redirectTo) {
                event.preventDefault();
                $state.go(to.redirectTo, params, { location: 'replace' })
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
                    $state.go("auth.login");
                    $rootScope.isAuth = false;
                },
                onError: function() {

                }
            };

            utilities.sendRequest(parameters);
        }
    };
})();
