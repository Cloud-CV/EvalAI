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

        var verify_email = {
            name: "auth.verify-email",
            parent: "auth",
            url: "/api/auth/registration/account-confirm-email/:email_conf_key",
            templateUrl: baseUrl + "/web/verify-email.html",
            title: "Email Verify",
            authenticate: false
        }

        var reset_password = {
            name: "auth.reset-password",
            parent: "auth",
            url: "/reset-password",
            templateUrl: baseUrl + "/web/reset-password.html",
            title: "Reset Password",
            authenticate: false
        }

        var reset_password_confirm = {
            name: "auth.reset-password-confirm",
            parent: "auth",
            url: "/api/password/reset/confirm/:user_id/:reset_token",
            templateUrl: baseUrl + "/web/reset-password-confirm.html",
            title: "Reset Password Confirm",
            authenticate: false
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
            title: 'Participating Teams',
            authenticate: true
        }

        var challenge_host_teams = {
            name: "web.challenge-host-teams",
            parent: "web",
            url: "/challenge-host-teams",
            templateUrl: baseUrl + "/web/challenge-host-teams.html",
            controller: 'ChallengeHostTeamsCtrl',
            controllerAs: 'challengeHostTeams',
            title: 'Host Teams',
            authenticate: true
        }

        var challenge_main = {
            name: "web.challenge-main",
            parent: "web",
            url: "/challenges",
            templateUrl: baseUrl + "/web/challenge-main.html",
            // controller: 'ChallengeMainCtrl',
            // controllerAs: 'challengeMain',
            redirectTo: "web.challenge-main.challenge-list",
            authenticate: true
        }

        var challenge_create = {
            name: "web.challenge-create",
            parent: "web",
            url: "/challenges/create",
            templateUrl: baseUrl + "/web/challenge-create.html",
            title: 'Create Challenge',
            controller: 'ChallengeCreateCtrl',
            controllerAs: 'challengeCreate',
            // redirectTo: "web.challenge-create.challenge-list",
            authenticate: true
        }

        var challenge_list = {
            name: "web.challenge-main.challenge-list",
            parent: "web.challenge-main",
            url: "/list",
            templateUrl: baseUrl + "/web/challenge/challenge-list.html",
            controller: 'ChallengeListCtrl',
            controllerAs: 'challengeList',
            title: 'Challenges',
            authenticate: true
        }

        var challenge_page = {
            name: "web.challenge-main.challenge-page",
            parent: "web.challenge-main",
            url: "/challenge-page/:challengeId",
            templateUrl: baseUrl + "/web/challenge-page.html",
            controller: 'ChallengeCtrl',
            controllerAs: 'challenge',
            redirectTo: "web.challenge-main.challenge-page.overview",
            authenticate: true
        }

        var overview = {
            name: "web.challenge-main.challenge-page.overview",
            parent: "web.challenge-main.challenge-page",
            url: "/overview",
            templateUrl: baseUrl + "/web/challenge/overview.html",
            title: 'Overview',
            authenticate: true
        }

        var evaluation = {
            name: "web.challenge-main.challenge-page.evaluation",
            url: "/evaluation",
            templateUrl: baseUrl + "/web/challenge/evaluation.html",
            title: 'Evaluation',
            authenticate: true
        }

        var phases = {
            name: "web.challenge-main.challenge-page.phases",
            url: "/phases",
            templateUrl: baseUrl + "/web/challenge/phases.html",
            title: 'Phases',
            authenticate: true
        }

        var participate = {
            name: "web.challenge-main.challenge-page.participate",
            url: "/participate",
            templateUrl: baseUrl + "/web/challenge/participate.html",
            title: 'Participate',
            authenticate: true
        }

        var submission = {
            name: "web.challenge-main.challenge-page.submission",
            url: "/submission",
            templateUrl: baseUrl + "/web/challenge/submission.html",
            title: 'Submission',
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

        var error_404 = {
            name: "error-404",
            templateUrl: baseUrl + "/web/error-pages/error-404.html",
            title: "Error 404",
        }



        // call all states here
        $stateProvider.state(home);

        // auth configs
        $stateProvider.state(auth);
        $stateProvider.state(login);
        $stateProvider.state(signup);
        $stateProvider.state(verify_email);
        $stateProvider.state(reset_password);
        $stateProvider.state(reset_password_confirm);
        $stateProvider.state(logout);

        // web main configs.
        $stateProvider.state(web);
        $stateProvider.state(dashboard);
        $stateProvider.state(teams);

        // challenge host teams
        $stateProvider.state(challenge_host_teams);

        // challenges list page
        $stateProvider.state(challenge_main);
        $stateProvider.state(challenge_list);

        // challenge create page
        $stateProvider.state(challenge_create);

        // challenge details
        $stateProvider.state(challenge_page);
        $stateProvider.state(overview);
        $stateProvider.state(evaluation);
        $stateProvider.state(phases);
        $stateProvider.state(participate);
        $stateProvider.state(submission);

        $stateProvider.state(host_challenge);

        $stateProvider.state(profile);
        $stateProvider.state(permission_denied);
        $stateProvider.state(change_password);
        $stateProvider.state(error_404);

        $urlRouterProvider.otherwise(function($injector, $location) {
            var state = $injector.get('$state');
            state.go('error-404');
            return $location.path();
        });
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

        var userKey = utilities.getData('userKey');

        $rootScope.logout = function() {

            var parameters = {};
            parameters.url = 'auth/logout/';
            parameters.method = 'POST';
            parameters.token = userKey;
            parameters.callback = {
                onSuccess: function(response) {
                    var status = response.status;
                    var response = response.data;
                    utilities.resetStorage();
                    $state.go("auth.login");
                    $rootScope.isAuth = false;
                },
                onError: function(response) {
                    var status = response.status;
                    var error = response.data;
                }
            };

            utilities.sendRequest(parameters);
        }

        checkToken = function() {
            var parameters = {};
            parameters.url = 'auth/user/';
            parameters.method = 'GET';
            parameters.token = userKey;
            parameters.callback = {
                onSuccess: function(response) {
                    var status = response.status;
                    var response = response.data;
                },
                onError: function(response) {
                    var status = response.status;
                    var error = response.data;
                    if (status == 401) {
                        alert("Timeout, Please login again to continue!")
                        utilities.resetStorage();
                        $state.go("auth.login");
                        $rootScope.isAuth = false;
                    }
                }
            };

            utilities.sendRequest(parameters);
        }

        console.log(utilities.isAuthenticated())
        if ($rootScope.isAuth == false) {
            // checkToken();
        }


    };
})();
