/**
 * Config for the router
 */

(function () {
    'use strict';
    angular
        .module('evalai')
        .config(configure);

    var baseUrl = "dist/views";

    configure.$inject = ['$stateProvider', '$urlRouterProvider', '$locationProvider', '$urlMatcherFactoryProvider'];

    function configure($stateProvider, $urlRouterProvider, $locationProvider, $urlMatcherFactoryProvider) {

        //in order to prevent 404 for trailing '/' in urls
        $urlMatcherFactoryProvider.strictMode(false);

        // formating hashed url
        $locationProvider.html5Mode({
            enabled: true,
            requireBase: true
        });

        // Index url definition
        var home = {
            name: "home",
            url: "/",
            templateUrl: baseUrl + "/web/landing.html",
            controller: 'MainCtrl',
            controllerAs: 'main',
            title: "Welcome"
        };

        // Auth related urls
        var auth = {
            name: "auth",
            url: "/auth",
            templateUrl: baseUrl + "/web/auth/auth.html",
            controller: 'AuthCtrl',
            controllerAs: 'auth',
            abstract: true,
            title: 'Auth'
        };

        var login = {
            name: "auth.login",
            parent: "auth",
            url: "/login",
            templateUrl: baseUrl + "/web/auth/login.html",
            title: 'Login',
            authpage: true
        };

        var signup = {
            name: "auth.signup",
            parent: "auth",
            url: "/signup",
            templateUrl: baseUrl + "/web/auth/signup.html",
            title: 'SignUp',
            authpage: true
        };

        var verify_email = {
            name: "auth.verify-email",
            parent: "auth",
            url: "/api/auth/registration/account-confirm-email/:email_conf_key",
            templateUrl: baseUrl + "/web/auth/verify-email.html",
            title: "Email Verify",
            authpage: true
        };

        var reset_password = {
            name: "auth.reset-password",
            parent: "auth",
            url: "/reset-password",
            templateUrl: baseUrl + "/web/auth/reset-password.html",
            title: "Reset Password",
            authpage: true
        };

        var reset_password_confirm = {
            name: "auth.reset-password-confirm",
            parent: "auth",
            url: "/api/password/reset/confirm/:user_id/:reset_token",
            templateUrl: baseUrl + "/web/auth/reset-password-confirm.html",
            title: "Reset Password Confirm",
            authpage: true
        };

        var logout = {
            name: "auth.logout",
            parent: "auth",
            url: "/logout",
            authenticate: true,
            title: 'Logout'
        };

        // main app 'web'
        var web = {
            name: "web",
            url: "/web",
            templateUrl: baseUrl + "/web/web.html",
            controller: 'WebCtrl',
            controllerAs: 'web',
            abstract: true
        };

        var dashboard = {
            name: "web.dashboard",
            parent: "web",
            url: "/dashboard",
            templateUrl: baseUrl + "/web/dashboard.html",
            controller: 'DashCtrl',
            controllerAs: 'dash',
            title: 'Dashboard',
            authenticate: true
        };

        var teams = {
            name: "web.teams",
            parent: "web",
            url: "/teams",
            templateUrl: baseUrl + "/web/teams.html",
            controller: 'TeamsCtrl',
            controllerAs: 'teams',
            title: 'Participating Teams',
            authenticate: true
        };

        var hosted_challenges = {
            name: "web.hosted-challenge",
            parent: "web",
            url: "/hosted-challenges",
            templateUrl: baseUrl + "/web/hosted-challenges.html",
            controller: 'HostedChallengesCtrl',
            controllerAs: 'hostedChallenges',
            title: 'Hosted Challenges',
            authenticate: true
        };

        var host_analytics = {
            name: "web.host-analytics",
            parent: "web",
            url: "/host-analytics",
            templateUrl: baseUrl + "/web/analytics/host-analytics.html",
            controller: 'AnalyticsCtrl',
            controllerAs: 'analytics',
            title: 'Host Challenge Analytics',
            authenticate: true
        };

        var challenge_host_teams = {
            name: "web.challenge-host-teams",
            parent: "web",
            url: "/challenge-host-teams",
            templateUrl: baseUrl + "/web/challenge-host-teams.html",
            controller: 'ChallengeHostTeamsCtrl',
            controllerAs: 'challengeHostTeams',
            title: 'Host Teams',
            authenticate: true
        };

        var challenge_create = {
            name: "web.challenge-create",
            parent: "web",
            url: "/challenge-create",
            templateUrl: baseUrl + "/web/challenge-create.html",
            title: 'Create Challenge',
            controller: 'ChallengeCreateCtrl',
            controllerAs: 'challengeCreate',
            authenticate: true
        };

        var challenge_main = {
            name: "web.challenge-main",
            parent: "web",
            url: "/challenges",
            templateUrl: baseUrl + "/web/challenge-main.html",
            redirectTo: "web.challenge-main.challenge-list",
        };

        var challenge_list = {
            name: "web.challenge-main.challenge-list",
            parent: "web.challenge-main",
            url: "/list",
            templateUrl: baseUrl + "/web/challenge-list.html",
            controller: 'ChallengeListCtrl',
            controllerAs: 'challengeList',
            title: 'Challenges',
        };

        var challenge_page = {
            name: "web.challenge-main.challenge-page",
            parent: "web.challenge-main",
            url: "/challenge-page/:challengeId",
            templateUrl: baseUrl + "/web/challenge/challenge-page.html",
            controller: 'ChallengeCtrl',
            controllerAs: 'challenge',
            redirectTo: "web.challenge-main.challenge-page.overview",
        };

        var overview = {
            name: "web.challenge-main.challenge-page.overview",
            parent: "web.challenge-main.challenge-page",
            url: "/overview",
            templateUrl: baseUrl + "/web/challenge/overview.html",
            title: 'Overview',
        };

        var evaluation = {
            name: "web.challenge-main.challenge-page.evaluation",
            parent: "web.challenge-main.challenge-page",
            url: "/evaluation",
            templateUrl: baseUrl + "/web/challenge/evaluation.html",
            title: 'Evaluation',
        };

        var phases = {
            name: "web.challenge-main.challenge-page.phases",
            parent: "web.challenge-main.challenge-page",
            url: "/phases",
            templateUrl: baseUrl + "/web/challenge/phases.html",
            title: 'Phases',
        };

        var participate = {
            name: "web.challenge-main.challenge-page.participate",
            parent: "web.challenge-main.challenge-page",
            url: "/participate",
            templateUrl: baseUrl + "/web/challenge/participate.html",
            title: 'Participate',
        };

        var submission = {
            name: "web.challenge-main.challenge-page.submission",
            parent: "web.challenge-main.challenge-page",
            url: "/submission",
            templateUrl: baseUrl + "/web/challenge/submission.html",
            title: 'Submit',
            authenticate: true
        };

        var my_submission = {
            name: "web.challenge-main.challenge-page.my-submission",
            parent: "web.challenge-main.challenge-page",
            url: "/my-submission",
            templateUrl: baseUrl + "/web/challenge/my-submission.html",
            title: 'My Submissions',
            authenticate: true
        };

        var my_challenge_all_submission = {
            name: "web.challenge-main.challenge-page.my-challenge-all-submission",
            parent: "web.challenge-main.challenge-page",
            url: "/my-challenge-all-submission",
            templateUrl: baseUrl + "/web/challenge/my-challenge-all-submission.html",
            title: 'My Challenge All Submissions',
            authenticate: true,
            resolve: {
              challenge: function(utilities, $state, $stateParams) {
                return new Promise(function(resolve, reject) {
                  var parameters = {};
                  parameters.token = utilities.getData('userKey');
                  parameters.url = 'participants/participant_teams/challenges/' + $stateParams.challengeId + '/user';
                  parameters.method = 'GET';
                  parameters.data = {};
                  parameters.callback = {
                    onSuccess: function(response) {
                      var details = response.data;
                      if (details.is_challenge_host) {
                        resolve(details);
                      } else {
                        $state.go('error-404');
                        reject();
                      }
                    },
                    onError: function() {
                      reject();
                    }
                  };
                  utilities.sendRequest(parameters);
                });
              }
            },
        }; 

        var approval_team = {
            name: "web.challenge-main.challenge-page.approval_team",
            parent: "web.challenge-main.challenge-page",
            url: "/approval_team",
            templateUrl: baseUrl + "/web/challenge/approval-team.html",
            title: 'My Challenge Approved Teams',
            authenticate: true,
            
        };

        var leaderboard = {
            name: "web.challenge-main.challenge-page.leaderboard",
            parent: "web.challenge-main.challenge-page",
            url: "/leaderboard",
            templateUrl: baseUrl + "/web/challenge/leaderboard.html",
            title: 'Leaderboard',
        };

        var manage = {
            name: "web.challenge-main.challenge-page.manage",
            parent: "web.challenge-main.challenge-page",
            url: "/manage",
            templateUrl: baseUrl + "/web/challenge/manage.html",
            controller: 'ChallengeCtrl',
            controllerAs: 'challenge',
            authenticate: true,
            resolve: {
              challenge: function(utilities, $state, $stateParams) {
                return new Promise(function(resolve, reject) {
                  var parameters = {};
                  parameters.token = utilities.getData('userKey');
                  parameters.url = 'participants/participant_teams/challenges/' + $stateParams.challengeId + '/user';
                  parameters.method = 'GET';
                  parameters.data = {};
                  parameters.callback = {
                    onSuccess: function(response) {
                      var details = response.data;
                      if (details.is_challenge_host) {
                        resolve(details);
                      } else {
                        $state.go('error-404');
                        reject();
                      }
                    },
                    onError: function() {
                      reject();
                    }
                  };
                  utilities.sendRequest(parameters);
                });
              }
            },
        }; 

        var challenge_phase_leaderboard = {
            name: "web.challenge-main.challenge-page.phase-leaderboard",
            url: "/leaderboard/:phaseSplitId",
            controller: 'ChallengeCtrl',
            controllerAs: 'challenge',
            templateUrl: baseUrl + "/web/challenge/leaderboard.html",
            title: 'Leaderboard'
        };

        var challenge_phase_metric_leaderboard = {
            name: "web.challenge-main.challenge-page.phase-metric-leaderboard",
            url: "/leaderboard/:phaseSplitId/:metric",
            controller: 'ChallengeCtrl',
            controllerAs: 'challenge',
            templateUrl: baseUrl + "/web/challenge/leaderboard.html",
            title: 'Leaderboard'
        };

        var profile = {
            name: "web.profile",
            parent: "web",
            url: "/profile",
            templateUrl: baseUrl + "/web/profile/profile.html",
            title: "Profile",
            controller: 'profileCtrl',
            controllerAs: 'profile',
            redirectTo: "web.profile.Updateprofile",
            authenticate: true
        };

        var auth_token = {
            name: "web.profile.AuthToken",
            parent: "web.profile",
            url: "/auth-token",
            templateUrl: baseUrl + "/web/auth/get-token.html",
            title: 'Auth Token',
            authenticate: true
        };

        var update_profile = {
            name: "web.profile.Updateprofile",
            parent: "web.profile",
            url: "/update-profile",
            templateUrl: baseUrl + "/web/profile/edit-profile/update-profile.html",
            title: 'Update profile',
            authenticate: true
        };

        var edit_profile = {
            name: "web.profile.Editprofile",
            parent: "web.profile",
            url: "/edit-profile",
            templateUrl: baseUrl + "/web/profile/edit-profile/edit-profile.html",
            title: 'Edit profile',
            authenticate: true
        };

        var deactivate_account = {
            name: "web.profile.deactivate-account",
            parent: "web.profile",
            url: "/deactivate-account",
            templateUrl: baseUrl + "/web/profile/edit-profile/deactivate-account.html",
            title: 'Deactivate Account',
            authenticate: true
        };

        var host_challenge = {
            name: "web.host-challenge",
            parent: "web",
            url: "/host-challenge",
            templateUrl: baseUrl + "/web/host-challenge.html",
            title: 'Host Competition',
            // controller: 'HostCtrl',
            // controllerAs: 'host',
            authenticate: true
        };

        var permission_denied = {
            name: "web.permission-denied",
            parent: "web",
            url: "/permission-denied",
            templateUrl: baseUrl + "/web/permission-denied.html",
            title: "Permission Denied",
            controller: 'PermCtrl',
            controllerAs: 'perm',
            authenticate: true
        };

        var change_password = {
            name: "web.profile.change-password",
            parent: "web.profile",
            url: "/change-password",
            templateUrl: baseUrl + "/web/change-password.html",
            title: "Change Password",
            controller: 'ChangePwdCtrl',
            controllerAs: 'changepwd',
            authenticate: true
        };

        var error_404 = {
            name: "error-404",
            templateUrl: baseUrl + "/web/error-pages/error-404.html",
            title: "Error 404",
        };

        var error_500 = {
            name: "error-500",
            templateUrl: baseUrl + "/web/error-pages/error-500.html",
            title: "Error 500",
        };

        var privacy_policy = {
            name: "privacy_policy",
            url: "/privacy-policy",
            templateUrl: baseUrl + "/web/privacy-policy.html",
            title: "Privacy Policy"
        };

        var about_us = {
            name: 'about-us',
            url: "/about",
            templateUrl: baseUrl + "/web/about-us.html",
            title: "About Us"
        };

        var our_team = {
            name: 'our-team',
            url: "/team",
            templateUrl: baseUrl + "/web/our-team.html",
            controller: 'ourTeamCtrl',
            controllerAs: 'ourTeam',
            title: "Team"
        };

        var get_involved = {
            name: 'get-involved',
            url: "/get-involved",
            templateUrl: baseUrl + "/web/get-involved.html",
            title: "Get Involved"
        };

        var contact_us = {
            name: "contact-us",
            url: "/contact",
            templateUrl: baseUrl + "/web/contact-us.html",
            title: "Contact Us",
            controller: 'contactUsCtrl',
            controllerAs: 'contactUs'
        };

        var featured_challenge_page = {
            name: "featured-challenge-page",
            url: "/featured-challenges/:challengeId",
            templateUrl: baseUrl + "/web/featured-challenge/challenge-page.html",
            controller: 'FeaturedChallengeCtrl',
            controllerAs: 'featured_challenge',
            redirectTo: "featured-challenge-page.overview"
        };

        var featured_challenge_overview = {
            name: "featured-challenge-page.overview",
            parent: "featured-challenge-page",
            url: "/overview",
            templateUrl: baseUrl + "/web/featured-challenge/overview.html",
            title: 'Overview'
        };

        var featured_challenge_evaluation = {
            name: "featured-challenge-page.evaluation",
            url: "/evaluation",
            templateUrl: baseUrl + "/web/featured-challenge/evaluation.html",
            title: 'Evaluation'
        };

        var featured_challenge_phases = {
            name: "featured-challenge-page.phases",
            url: "/phases",
            templateUrl: baseUrl + "/web/featured-challenge/phases.html",
            title: 'Phases'
        };

        var featured_challenge_participate = {
            name: "featured-challenge-page.participate",
            url: "/participate",
            templateUrl: baseUrl + "/web/featured-challenge/participate.html",
            title: 'Participate'
        };

        var featured_challenge_leaderboard = {
            name: "featured-challenge-page.leaderboard",
            url: "/leaderboard",
            templateUrl: baseUrl + "/web/featured-challenge/leaderboard.html",
            title: 'Leaderboard'
        };

        var featured_challenge_phase_leaderboard = {
            name: "featured-challenge-page.phase-leaderboard",
            url: "/leaderboard/:phaseSplitId",
            controller: 'FeaturedChallengeCtrl',
            controllerAs: 'featured_challenge',
            templateUrl: baseUrl + "/web/featured-challenge/leaderboard.html",
            title: 'Leaderboard'
        };

        var challengeInvitation = {
            name: "challenge-invitation",
            url: "/accept-invitation/:invitationKey",
            controller: "ChallengeInviteCtrl",
            controllerAs: "challenge_invitation",
            templateUrl: baseUrl + "/web/challenge-invite.html",
            title: "Accept challenge invitation"
        };

        var get_submission_related_files = {
            name: "get-submission-related-files",
            url: "/web/submission-files?bucket&key",
            controller: "SubmissionFilesCtrl",
            controllerAs: "submission_files",
        };

        // call all states here
        $stateProvider.state(home);
        $stateProvider.state(privacy_policy);

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
        $stateProvider.state(host_analytics);
        $stateProvider.state(teams);
        $stateProvider.state(hosted_challenges);

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
        $stateProvider.state(my_submission);
        $stateProvider.state(my_challenge_all_submission);
        $stateProvider.state(approval_team);
        $stateProvider.state(leaderboard);
        $stateProvider.state(challenge_phase_leaderboard);
        $stateProvider.state(challenge_phase_metric_leaderboard);

        // featured challenge details
        $stateProvider.state(featured_challenge_page);
        $stateProvider.state(featured_challenge_overview);
        $stateProvider.state(featured_challenge_evaluation);
        $stateProvider.state(featured_challenge_phases);
        $stateProvider.state(featured_challenge_participate);
        $stateProvider.state(featured_challenge_leaderboard);
        $stateProvider.state(featured_challenge_phase_leaderboard);

        $stateProvider.state(host_challenge);

        $stateProvider.state(profile);
        $stateProvider.state(auth_token);
        $stateProvider.state(update_profile);
        $stateProvider.state(permission_denied);
        $stateProvider.state(change_password);
        $stateProvider.state(error_404);
        $stateProvider.state(error_500);
        $stateProvider.state(about_us);
        $stateProvider.state(our_team);
        $stateProvider.state(get_involved);
        $stateProvider.state(edit_profile);
        $stateProvider.state(deactivate_account);
        $stateProvider.state(contact_us);
        $stateProvider.state(challengeInvitation);
        $stateProvider.state(get_submission_related_files);

        $stateProvider.state(manage);

        $urlRouterProvider.otherwise(function($injector, $location) {
            var state = $injector.get('$state');
            state.go('error-404');
            return $location.path();
        });
    }

})();

// define run block here
(function () {
    
    'use strict';

    angular
        .module('evalai')
        .run(runFunc);

    runFunc.$inject = ['$rootScope', '$state', 'utilities', '$window', '$location', 'toaster'];
    
    function runFunc($rootScope, $state, utilities, $window, $location, toaster) {
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
        $rootScope.$on("$stateChangeStart", function(event, to, toParams) {
            if (utilities.isAuthenticated()) {
                $rootScope.isAuth = true;
                if (to.authpage) {
                    event.preventDefault();
                    $state.go("home");
                }
            } else {
                $rootScope.isAuth = false;
                if (to.authenticate) {
                    event.preventDefault();
                    $rootScope.previousState = to;
                    $rootScope.previousStateParams = toParams;
                    $state.go("auth.login");
                }
            }

        });

        $rootScope.$on('$stateChangeStart', function(event, to, params) {
            if (to.redirectTo) {
                event.preventDefault();
                $state.go(to.redirectTo, params, { location: $location.path() });
            }
        });

        $rootScope.$on('$stateChangeSuccess', function() {
            // Save the route title
            $rootScope.pageTitle = $state.current.title;
            // Scroll to top
            $window.scrollTo(0, 0);
            // Google Analytics Scripts
            if ($window.ga) {
                $window.ga('create', 'UA-45466017-2', 'auto');
                $window.ga('send', 'pageview', $location.path());
            }
        });

        $rootScope.notify = function(type, message, timeout) {
            // function to pic timeout
            function pick(arg, def) {
                return (typeof arg === undefined ? def : arg);
            }

            timeout = pick(timeout, 5000);
            toaster.pop({
                type: type,
                body: message,
                timeout: timeout,
            });
        };

        $rootScope.logout = function() {
            var userKey = utilities.getData('userKey');
            var parameters = {};
            parameters.url = 'auth/logout/';
            parameters.method = 'POST';
            parameters.token = userKey;
            parameters.callback = {
                onSuccess: function() {
                    utilities.resetStorage();
                    $rootScope.isLoader = false;
                    $state.go("home");
                    $rootScope.isAuth = false;
                    $rootScope.notify("info", "Successfully logged out!");
                },
                onError: function() {}
            };

            utilities.sendRequest(parameters);
        };

        $rootScope.checkToken = function() {
            var userKey = utilities.getData('userKey');
            var parameters = {};
            parameters.url = 'auth/user/';
            parameters.method = 'GET';
            parameters.token = userKey;
            parameters.callback = {
                onSuccess: function() {},
                onError: function(response) {
                    var status = response.status;
                    if (status == 401) {
                        alert("Timeout, Please login again to continue!");
                        utilities.resetStorage();
                        $state.go("auth.login");
                        $rootScope.isAuth = false;
                    }
                }
            };

            utilities.sendRequest(parameters);
        };

        if (!$rootScope.isAuth) {
            // checkToken();
        }
    }
})();
