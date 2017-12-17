// Invoking IIFE for dashboard
(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('AnalyticsCtrl', AnalyticsCtrl);

    AnalyticsCtrl.$inject = ['utilities', '$state', '$rootScope'];

    function AnalyticsCtrl(utilities, $state, $rootScope) {
        var vm = this;

        vm.hostTeam = {};
        vm.teamId = null;
        vm.currentTeamName = null;
        vm.challengeListCount = 0;
        vm.challengeList = {};
        vm.challengeAnalysisDetail = {};
        vm.isTeamSelected = false;
        vm.challengeId = null;
        vm.currentChallengeDetails = {};
        vm.currentPhase = [];
        vm.totalSubmission = {};
        vm.totalParticipatedTeams = {};
        vm.lastSubmissionTime = {};

        var userKey = utilities.getData('userKey');

        var parameters = {};
        parameters.url = 'hosts/challenge_host_team/';
        parameters.method = 'GET';
        parameters.token = userKey;
        parameters.callback = {
            onSuccess: function(response) {
                var status = response.status;
                var details = response.data;
                if (status == 200) {
                    vm.hostTeam = details.results;

                }
            },
            onError: function(response) {
                var status = response.status;
                var error = response.data;
                if (status == 403) {
                    vm.error = error;

                    // navigate to permissions denied page
                    $state.go('web.permission-denied');
                } else if (status == 401) {
                    alert("Timeout, Please login again to continue!");
                    utilities.resetStorage();
                    $state.go("auth.login");
                    $rootScope.isAuth = false;

                }
            }
        };
        utilities.sendRequest(parameters);


        parameters.url = 'challenges/challenge?mode=host';
        parameters.method = 'GET';
        parameters.token = userKey;
        parameters.callback = {
            onSuccess: function(response) {
                var status = response.status;
                var details = response.data;
                if (status == 200) {
                    vm.challengeList = details.results;
                    vm.challengeListCount = details.count;
                }
            },
            onError: function(response) {
                var status = response.status;
                var error = response.data;
                if (status == 403) {
                    vm.error = error;

                    // navigate to permissions denied page
                    $state.go('web.permission-denied');
                } else if (status == 401) {
                    alert("Timeout, Please login again to continue!");
                    utilities.resetStorage();
                    $state.go("auth.login");
                    $rootScope.isAuth = false;

                }
            }
        };
        utilities.sendRequest(parameters);

        vm.showChallengeAnalysis = function() {
            if (vm.challengeId != null) {
                parameters.url = 'challenges/challenge/' + vm.challengeId + '/challenge_phase';
                parameters.method = 'GET';
                parameters.token = userKey;
                parameters.callback = {
                    onSuccess: function(response) {
                        var status = response.status;
                        var details = response.data;


                        if (status === 200) {
                            vm.currentPhase = details.results;
                            var challengePhaseId = [];
                            for (var phaseCount = 0; phaseCount < vm.currentPhase.length; phaseCount++) {
                                parameters.url = 'analytics/challenge/' + vm.challengeId + '/challenge_phase/' +  vm.currentPhase[phaseCount].id + '/count';
                                parameters.method = 'GET';
                                parameters.token = userKey;
                                challengePhaseId.push(vm.currentPhase[phaseCount].id);
                                parameters.callback = {
                                    onSuccess: function(response) {
                                        var status = response.status;
                                        var details = response.data;
                                        if (status == 200) {
                                            for(var i=0; i<challengePhaseId.length; i++) {
                                                if (challengePhaseId[i] == details.challenge_phase) {
                                                    vm.totalSubmission[challengePhaseId[i]] = details.submission_count;
                                                    vm.totalParticipatedTeams[challengePhaseId[i]] = details.participant_team_count;
                                                    i++;
                                                    break;
                                                }
                                            }
                                        }
                                    },
                                    onError: function(response) {
                                        var status = response.status;
                                        var error = response.data;
                                        if (status == 403) {
                                            vm.error = error;

                                            // navigate to permissions denied page
                                            $state.go('web.permission-denied');
                                        } else if (status == 401) {
                                            alert("Timeout, Please login again to continue!");
                                            utilities.resetStorage();
                                            $state.go("auth.login");
                                            $rootScope.isAuth = false;

                                        }
                                    }
                                };
                                utilities.sendRequest(parameters);
                            }

                            for (phaseCount = 0; phaseCount < vm.currentPhase.length; phaseCount++) {
                                parameters.url = 'analytics/challenge/' + vm.challengeId + '/challenge_phase/' +  vm.currentPhase[phaseCount].id + '/last_submission_datetime_analysis/';
                                parameters.method = 'GET';
                                parameters.token = userKey;
                                challengePhaseId.push(vm.currentPhase[phaseCount].id);
                                parameters.callback = {
                                    onSuccess: function(response) {
                                        var status = response.status;
                                        var details = response.data;
                                        if (status == 200) {
                                            for(var i=0; i<challengePhaseId.length; i++) {
                                                if (challengePhaseId[i] == response.data.challenge_phase) {
                                                    vm.lastSubmissionTime[challengePhaseId[i]] = details.last_submission_timestamp_in_challenge_phase;
                                                    i++;
                                                    break;
                                                }
                                            }
                                        }
                                    },
                                    onError: function(response) {
                                        var status = response.status;
                                        var error = response.data;
                                        if (status == 403) {
                                            vm.error = error;

                                            // navigate to permissions denied page
                                            $state.go('web.permission-denied');
                                        } else if (status == 401) {
                                            alert("Timeout, Please login again to continue!");
                                            utilities.resetStorage();
                                            $state.go("auth.login");
                                            $rootScope.isAuth = false;

                                        }
                                    }
                                };
                                utilities.sendRequest(parameters);
                            }

                        }
                    },
                    onError: function(response) {
                        var status = response.status;
                        var error = response.data;
                        if (status == 403) {
                            vm.error = error;

                            // navigate to permissions denied page
                            $state.go('web.permission-denied');
                        } else if (status == 401) {
                            alert("Timeout, Please login again to continue!");
                            utilities.resetStorage();
                            $state.go("auth.login");
                            $rootScope.isAuth = false;

                        }
                    }
                };

                utilities.sendRequest(parameters);
                vm.isTeamSelected = true;
                for (var i = 0; i < vm.challengeList.length; i++) {

                    if (vm.challengeList[i].id == vm.challengeId) {
                        vm.currentChallengeDetails = vm.challengeList[i];
                    }
                }
            } else {
                vm.isTeamSelected = false;
            }
        };
    }

})();

// Invoking IIFE for auth
(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('AuthCtrl', AuthCtrl);

    AuthCtrl.$inject = ['utilities', '$state', '$rootScope', '$timeout'];

    function AuthCtrl(utilities, $state, $rootScope) {
        var vm = this;

        vm.isRem = false;
        vm.isAuth = false;
        vm.isMail = true;
        vm.userMail = '';
        // getUser for signup
        vm.regUser = {};
        // useDetails for login
        vm.getUser = {};
        vm.isResetPassword = false;
        // form error
        vm.isFormError = false;
        vm.FormError = {};
        // to store the next redirect route
        vm.redirectUrl = {};

        // default parameters
        vm.isLoader = false;
        vm.isPassConf = true;
        vm.wrnMsg = {};
        vm.isValid = {};
        vm.confirmMsg = '';
        $rootScope.loaderTitle = '';
        vm.loginContainer = angular.element('.auth-container');

        // show loader
        vm.startLoader = function(msg) {
            $rootScope.isLoader = true;
            $rootScope.loaderTitle = msg;
            vm.loginContainer.addClass('low-screen');
        };

        // stop loader
        vm.stopLoader = function() {
            $rootScope.isLoader = false;
            $rootScope.loaderTitle = '';
            vm.loginContainer.removeClass('low-screen');
        };

        vm.resetForm = function() {
            // getUser for signup
            vm.regUser = {};
            // useDetails for login
            vm.getUser = {};

            //reset error msg
            vm.wrnMsg = {};

            //switch off form errors
            vm.isFormError = false;

            //reset form when link sent for reset password
            vm.isMail = true;
        };

        // Function to signup
        vm.userSignUp = function(signupFormValid) {
            if (signupFormValid) {
                vm.startLoader("Setting up your details!");
                // call utility service
                var parameters = {};
                parameters.url = 'auth/registration/';
                parameters.method = 'POST';
                parameters.data = {
                    "username": vm.regUser.name,
                    "password1": vm.regUser.password,
                    "password2": vm.regUser.confirm_password,
                    "email": vm.regUser.email
                };
                parameters.callback = {
                    onSuccess: function(response) {
                        if (response.status == 201) {
                            vm.isFormError = false;
                            // vm.regMsg = "Registered successfully, Login to continue!";
                            $rootScope.notify("success", "Registered successfully. Please verify your email address!");
                            $state.go('auth.login');
                        }
                        vm.stopLoader();
                    },
                    onError: function(response) {
                        if (response.status == 400) {
                            vm.stopLoader();
                            vm.isFormError = true;
                            var non_field_errors, isUsername_valid, isEmail_valid, isPassword1_valid, isPassword2_valid;
                            try {
                                non_field_errors = typeof(response.data.non_field_errors) !== 'undefined' ? true : false;
                                isUsername_valid = typeof(response.data.username) !== 'undefined' ? true : false;
                                isEmail_valid = typeof(response.data.email) !== 'undefined' ? true : false;
                                isPassword1_valid = typeof(response.data.password1) !== 'undefined' ? true : false;
                                isPassword2_valid = typeof(response.data.password2) !== 'undefined' ? true : false;
                                if (non_field_errors) {
                                    vm.FormError = response.data.non_field_errors[0];
                                } else if (isUsername_valid) {
                                    vm.FormError = response.data.username[0];
                                } else if (isEmail_valid) {
                                    vm.FormError = response.data.email[0];
                                } else if (isPassword1_valid) {
                                    vm.FormError = response.data.password1[0];
                                } else if (isPassword2_valid) {
                                    vm.FormError = response.data.password2[0];

                                }

                            } catch (error) {
                                $rootScope.notify("error", error);
                            }
                        }

                        vm.stopLoader();
                    }
                };
                utilities.sendRequest(parameters, "no-header");
            } else {
                vm.stopLoader();
            }
        };

        // Function to login
        vm.userLogin = function(loginFormValid) {
            if (loginFormValid) {
                vm.startLoader("Taking you to EvalAI!");
                // call utility service
                var parameters = {};
                parameters.url = 'auth/login/';
                parameters.method = 'POST';
                parameters.data = {
                    "username": vm.getUser.name,
                    "password": vm.getUser.password,
                };
                parameters.callback = {
                    onSuccess: function(response) {
                        if (response.status == 200) {
                            utilities.storeData('userKey', response.data.token);
                            if ($rootScope.previousState) {
                                $state.go($rootScope.previousState);
                                vm.stopLoader();
                            }else {
                                $state.go('web.dashboard');
                            }
                        } else {
                            alert("Something went wrong");
                        }
                    },
                    onError: function(response) {
                        if (response.status == 400) {
                            vm.isFormError = true;
                            var non_field_errors;
                            try {
                                non_field_errors = typeof(response.data.non_field_errors) !== 'undefined' ? true : false;
                                if (non_field_errors) {
                                    vm.FormError = response.data.non_field_errors[0];
                                }
                            } catch (error) {
                                $rootScope.notify("error", error);
                            }
                        }
                        vm.stopLoader();
                    }
                };
                utilities.sendRequest(parameters, "no-header");
            } else {
                vm.stopLoader();
            }
        };

        // function to Verify Email
        vm.verifyEmail = function() {
            vm.startLoader("Verifying Your Email");
            var parameters = {};
            parameters.url = 'auth/registration/account-confirm-email/' + $state.params.email_conf_key + '/';
            parameters.method = 'GET';
            parameters.callback = {
                onSuccess: function() {
                    vm.email_verify_msg = "Your email has been verified successfully";
                    vm.stopLoader();
                },
                onError: function() {
                    vm.email_verify_msg = "Something went wrong!! Please try again.";
                    vm.stopLoader();
                }
            };

            utilities.sendRequest(parameters, "no-header");
        };

        // function to reset password
        vm.resetPassword = function(resetPassFormValid) {
            if (resetPassFormValid) {
                vm.startLoader("Sending Mail");
                var parameters = {};
                parameters.url = 'auth/password/reset/';
                parameters.method = 'POST';
                parameters.data = {
                    "email": vm.getUser.email,
                };
                parameters.callback = {
                    onSuccess: function(response) {
                        vm.isMail = false;
                        vm.getUser.error = false;
                        vm.isFormError = false;
                        vm.deliveredMsg = response.data.success;
                        vm.getUser.email = '';
                        vm.stopLoader();
                    },
                    onError: function() {
                        vm.isFormError = true;
                        vm.FormError = "Something went wrong. Please try again";
                        vm.stopLoader();
                    }
                };
                utilities.sendRequest(parameters, "no-header");
            } else {
                vm.stopLoader();
            }
        };

        // function to reset password confirm
        vm.resetPasswordConfirm = function(resetconfirmFormValid) {
            if (resetconfirmFormValid) {
                vm.startLoader("Resetting Your Password");
                var parameters = {};
                parameters.url = 'auth/password/reset/confirm/';
                parameters.method = 'POST';
                parameters.data = {
                    "new_password1": vm.getUser.new_password1,
                    "new_password2": vm.getUser.new_password2,
                    "uid": $state.params.user_id,
                    "token": $state.params.reset_token,
                };

                parameters.callback = {
                    onSuccess: function(response) {
                        var details = response.data;
                        vm.isResetPassword = true;
                        vm.deliveredMsg = details.detail;
                        vm.stopLoader();
                    },
                    onError: function(response) {
                        var token_valid, password1_valid, password2_valid;
                        vm.isFormError = true;
                        try {
                            token_valid = typeof(response.data.token) !== 'undefined' ? true : false;
                            password1_valid = typeof(response.data.new_password1) !== 'undefined' ? true : false;
                            password2_valid = typeof(response.data.new_password2) !== 'undefined' ? true : false;
                            if (token_valid) {
                                vm.FormError = "this link has been already used or expired.";
                            } else if (password1_valid) {
                                vm.FormError = Object.values(response.data.new_password1).join(" ");
                            } else if (password2_valid) {
                                vm.FormError = Object.values(response.data.new_password2).join(" ");
                            }
                        } catch (error) {
                            vm.FormError = "Something went wrong! Please refresh the page and try again.";
                        }
                        vm.stopLoader();
                    }
                };

                utilities.sendRequest(parameters, "no-header");
            } else {
                vm.stopLoader();
            }
        };

        $rootScope.$on('$stateChangeStart', function() {
            vm.resetForm();
        });
    }
})();

// Invoking IIFE for create challenge page
(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('ChallengeCreateCtrl', ChallengeCreateCtrl);

    ChallengeCreateCtrl.$inject = ['utilities', 'loaderService', '$rootScope', '$state'];

    function ChallengeCreateCtrl(utilities, loaderService, $rootScope, $state) {
        var vm = this;
        var userKey = utilities.getData('userKey');
        var hostTeamId = utilities.getData('challengeHostTeamId');
        vm.wrnMsg = {};
        vm.isValid = {};
        vm.isFormError = false;
        vm.input_file = null;
        vm.formError = {};

        // start loader
        vm.startLoader = loaderService.startLoader;

        // stop loader
        vm.stopLoader = loaderService.stopLoader;

        // function to create a challenge using zip file.
    vm.challengeCreate = function() {
            if (hostTeamId) {
                var fileVal = angular.element(".file-path").val();

                if (fileVal === null || fileVal === "") {
                    vm.isFormError = true;
                    vm.formError = "Please upload file!";
                }
                if (vm.input_file) {
                    var parameters = {};
                    parameters.url = 'challenges/challenge/challenge_host_team/' + hostTeamId + '/zip_upload/';
                    parameters.method = 'POST';
                    var formData = new FormData();
                    formData.append("zip_configuration", vm.input_file);

                    parameters.data = formData;

                    parameters.token = userKey;
                    parameters.callback = {
                        onSuccess: function(response) {
                            var status = response.status;
                            var details =  response.data;
                            if (status === 201) {
                                var inputTypeFile = "input[type='file']";
                                angular.forEach(
                                    angular.element(inputTypeFile),
                                    function(inputElem) {
                                        angular.element(inputElem).val(null);
                                    }
                                );

                                angular.element(".file-path").val(null);
                                $rootScope.notify("success", details.success);
                                localStorage.removeItem('challengeHostTeamId');
                                $state.go('home');
                            }
                        },
                        onError: function(response) {
                            var error = response.data;
                            angular.element(".file-path").val(null);
                            $rootScope.notify("error", error.error);
                            vm.stopLoader();
                        }
                    };
                }
                utilities.sendRequest(parameters, 'header', 'upload');
            }
            else {
                angular.element(".file-path").val(null);
                $rootScope.notify("info", "Please select a challenge host team!");
            }
        };
    }
})();


// Invoking IIFE for challenge page
(function() {

    'use strict';
    angular
        .module('evalai')
        .controller('ChallengeCtrl', ChallengeCtrl);

    ChallengeCtrl.$inject = ['utilities', 'loaderService', '$scope', '$state', '$http', '$stateParams', '$rootScope', 'Upload', '$interval', '$mdDialog'];

    function ChallengeCtrl(utilities, loaderService, $scope, $state, $http, $stateParams, $rootScope, Upload, $interval, $mdDialog) {
        var vm = this;
        vm.challengeId = $stateParams.challengeId;
        vm.phaseId = null;
        vm.phaseSplitId = null;
        vm.input_file = null;
        vm.methodName = null;
        vm.methodDesc = null;
        vm.projectUrl = null;
        vm.publicationUrl = null;
        vm.wrnMsg = {};
        vm.page = {};
        vm.isParticipated = false;
        vm.isActive = false;
        vm.phases = {};
        vm.phaseSplits = {};
        vm.isValid = {};
        vm.submissionVisibility = {};
        vm.showUpdate = false;
        vm.showLeaderboardUpdate = false;
        vm.poller = null;
        vm.isChallengeHost = false;
        vm.stopLeaderboard = function() {};
        vm.stopFetchingSubmissions = function() {};
        vm.currentDate = null;


        // loader for existing teams
        vm.isExistLoader = false;
        vm.loaderTitle = '';
        vm.loaderContainer = angular.element('.exist-team-card');

        // show loader
        vm.startLoader =  loaderService.startLoader;
        // stop loader
        vm.stopLoader = loaderService.stopLoader;

        var userKey = utilities.getData('userKey');

        vm.subErrors = {};

        utilities.showLoader();

        // get details of the particular challenge
        var parameters = {};
        parameters.url = 'challenges/challenge/' + vm.challengeId + '/';
        parameters.method = 'GET';
        parameters.data = {};
        parameters.token = userKey;
        parameters.callback = {
            onSuccess: function(response) {
                var details = response.data;
                vm.page = details;
                vm.isActive = details.is_active;


                if (vm.page.image === null) {
                    vm.page.image = "dist/images/logo.png";

                }

                if (vm.isActive) {

                    // get details of challenges corresponding to participant teams of that user
                    var parameters = {};
                    parameters.url = 'participants/participant_teams/challenges/'+ vm.challengeId + '/user';
                    parameters.method = 'GET';
                    parameters.data = {};
                    parameters.token = userKey;
                    parameters.callback = {
                        onSuccess: function(response) {
                            var details = response.data;
                            vm.currentDate = details.datetime_now;
                            for (var i in details.challenge_participant_team_list) {
                                if (details.challenge_participant_team_list[i].challenge !== null && details.challenge_participant_team_list[i].challenge.id == vm.challengeId) {
                                    vm.isParticipated = true;
                                    break;
                                }
                            }

                            if (details.is_challenge_host) {
                                vm.isChallengeHost = true;
                            }

                            if (!vm.isParticipated) {

                                vm.team = {};
                                vm.teamId = null;
                                vm.existTeam = {};
                                vm.currentPage = '';
                                vm.isNext = '';
                                vm.isPrev = '';
                                vm.team.error = false;

                                var parameters = {};
                                parameters.url = 'participants/participant_team';
                                parameters.method = 'GET';
                                parameters.token = userKey;
                                parameters.callback = {
                                    onSuccess: function(response) {
                                        var status = response.status;
                                        var details = response.data;
                                        if (status == 200) {
                                            vm.existTeam = details;

                                            // clear error msg from storage
                                            utilities.deleteData('emailError');

                                            // condition for pagination
                                            if (vm.existTeam.next === null) {
                                                vm.isNext = 'disabled';
                                            } else {
                                                vm.isNext = '';
                                            }

                                            if (vm.existTeam.previous === null) {
                                                vm.isPrev = 'disabled';
                                            } else {
                                                vm.isPrev = '';
                                            }
                                            if (vm.existTeam.next !== null) {
                                                vm.currentPage = vm.existTeam.next.split('page=')[1] - 1;
                                            }


                                            // select team from existing list
                                            vm.selectExistTeam = function() {

                                                // loader for exisiting teams
                                                vm.isExistLoader = true;
                                                vm.loaderTitle = '';
                                                vm.loaderContainer = angular.element('.exist-team-card');

                                                // show loader
                                                vm.startLoader("Loading Teams");
                                                // loader end

                                                var parameters = {};
                                                parameters.url = 'challenges/challenge/' + vm.challengeId + '/participant_team/' + vm.teamId;
                                                parameters.method = 'POST';
                                                parameters.token = userKey;
                                                parameters.callback = {
                                                    onSuccess: function() {
                                                        vm.isParticipated = true;
                                                        $state.go('web.challenge-main.challenge-page.submission');
                                                        vm.stopLoader();
                                                    },
                                                    onError: function(response) {
                                                        if (response.data['detail']) {
                                                            var error = "Please select a team first!";
                                                        } else if (response.data['error']) {
                                                            error = response.data['error'];
                                                        }
                                                        $rootScope.notify("error", error);
                                                        vm.stopLoader();
                                                    }
                                                };
                                                utilities.sendRequest(parameters);
                                            };

                                            // to load data with pagination
                                            vm.load = function(url) {
                                                // loader for exisiting teams
                                                vm.isExistLoader = true;
                                                vm.loaderTitle = '';
                                                vm.loaderContainer = angular.element('.exist-team-card');


                                                vm.startLoader("Loading Teams");
                                                if (url !== null) {

                                                    //store the header data in a variable
                                                    var headers = {
                                                        'Authorization': "Token " + userKey
                                                    };

                                                    //Add headers with in your request
                                                    $http.get(url, { headers: headers }).then(function(response) {
                                                        // reinitialized data
                                                        var details = response.data;
                                                        vm.existTeam = details;

                                                        // condition for pagination
                                                        if (vm.existTeam.next === null) {
                                                            vm.isNext = 'disabled';
                                                            vm.currentPage = vm.existTeam.count / 10;
                                                        } else {
                                                            vm.isNext = '';
                                                            vm.currentPage = parseInt(vm.existTeam.next.split('page=')[1] - 1);
                                                        }

                                                        if (vm.existTeam.previous === null) {
                                                            vm.isPrev = 'disabled';
                                                        } else {
                                                            vm.isPrev = '';
                                                        }
                                                        vm.stopLoader();
                                                    });
                                                }
                                            };

                                        }
                                        utilities.hideLoader();
                                    },
                                    onError: function(response) {
                                        var error = response.data;
                                        utilities.storeData('emailError', error.detail);
                                        $state.go('web.permission-denied');
                                        utilities.hideLoader();
                                    }
                                };

                                utilities.sendRequest(parameters);

                            }
                            // This condition means that the user is eligible to make submissions
                            // else if (vm.isParticipated) {

                            // }
                            utilities.hideLoader();
                        },
                        onError: function() {
                            utilities.hideLoader();
                        }
                    };

                    utilities.sendRequest(parameters);
                }

                utilities.hideLoader();

            },
            onError: function(response) {
                var error = response.data;
                utilities.storeData('emailError', error.detail);
                $state.go('web.permission-denied');
                utilities.hideLoader();
            }
        };

        utilities.sendRequest(parameters);

        vm.makeSubmission = function() {
            if (vm.isParticipated) {


                var fileVal = angular.element(".file-path").val();

                if (fileVal === null || fileVal === "") {
                    vm.subErrors.msg = "Please upload file!";
                } else {
                    vm.isExistLoader = true;
                    vm.loaderTitle = '';
                    vm.loaderContainer = angular.element('.exist-team-card');


                    vm.startLoader("Making Submission");
                    if (vm.input_file) {
                        // vm.upload(vm.input_file);
                    }
                    var parameters = {};
                    parameters.url = 'jobs/challenge/' + vm.challengeId + '/challenge_phase/' + vm.phaseId + '/submission/';
                    parameters.method = 'POST';
                    var formData = new FormData();
                    formData.append("status", "submitting");
                    formData.append("input_file", vm.input_file);
                    formData.append("method_name", vm.methodName);
                    formData.append("method_description", vm.methodDesc);
                    formData.append("project_url", vm.projectUrl);
                    formData.append("publication_url", vm.publicationUrl);

                    parameters.data = formData;

                    parameters.token = userKey;
                    parameters.callback = {
                        onSuccess: function() {
                            // vm.input_file.name = '';

                            angular.forEach(
                                angular.element("input[type='file']"),
                                function(inputElem) {
                                    angular.element(inputElem).val(null);
                                }
                            );

                            angular.element(".file-path").val(null);


                            vm.phaseId = null;
                            vm.methodName = null;
                            vm.methodDesc = null;
                            vm.projectUrl = null;
                            vm.publicationUrl = null;
                            // vm.subErrors.msg = "Your submission has been recorded succesfully!";
                            $rootScope.notify("success", "Your submission has been recorded succesfully!");

                            vm.stopLoader();
                        },
                        onError: function(response) {
                            var status = response.status;
                            var error = response.data;

                            vm.phaseId = null;
                            vm.methodName = null;
                            vm.methodDesc = null;
                            vm.projectUrl = null;
                            vm.publicationUrl = null;
                            if (status == 404) {

                                vm.subErrors.msg = "Please select phase!";
                            } else if (status == 400) {
                                vm.subErrors.msg = error.input_file[0];
                            } else {
                                vm.subErrors.msg = error.error;
                            }
                            vm.stopLoader();
                        }
                    };

                    utilities.sendRequest(parameters, 'header', 'upload');
                }
            }
        };



        // get details of the particular challenge phase
        parameters = {};
        parameters.url = 'challenges/challenge/' + vm.challengeId + '/challenge_phase';
        parameters.method = 'GET';
        parameters.data = {};
        parameters.token = userKey;
        parameters.callback = {
            onSuccess: function(response) {
                var details = response.data;
                vm.phases = details;
                // navigate to challenge page
                // $state.go('web.challenge-page.overview');
                utilities.hideLoader();
            },
            onError: function(response) {
                var error = response.data;
                utilities.storeData('emailError', error.detail);
                $state.go('web.permission-denied');
                utilities.hideLoader();
            }
        };

        utilities.sendRequest(parameters);

        // get details of the particular challenge phase split
        parameters = {};
        parameters.url = 'challenges/' + vm.challengeId + '/challenge_phase_split';
        parameters.method = 'GET';
        parameters.data = {};
        parameters.token = userKey;
        parameters.callback = {
            onSuccess: function(response) {
                var details = response.data;
                vm.phaseSplits = details;
                utilities.hideLoader();
            },
            onError: function(response) {
                var error = response.data;
                utilities.storeData('emailError', error.detail);
                $state.go('web.permission-denied');
                utilities.hideLoader();
            }
        };

        utilities.sendRequest(parameters);

        // my submissions
        vm.isResult = false;

        vm.getLeaderboard = function(phaseSplitId) {
            vm.stopLeaderboard = function() {
                $interval.cancel(vm.poller);
            };
            vm.stopLeaderboard();

            vm.isResult = true;
            vm.phaseSplitId = phaseSplitId;
            // loader for exisiting teams
            vm.isExistLoader = true;
            vm.loaderTitle = '';
            vm.loaderContainer = angular.element('.exist-team-card');

            vm.startLoader("Loading Leaderboard Items");


            // Show leaderboard
            vm.leaderboard = {};
            var parameters = {};
            parameters.url = "jobs/" + "challenge_phase_split/" + vm.phaseSplitId + "/leaderboard/?page_size=1000";
            parameters.method = 'GET';
            parameters.data = {};
            parameters.token = userKey;
            parameters.callback = {
                onSuccess: function(response) {
                    var details = response.data;
                    vm.leaderboard = details.results;

                    vm.startLeaderboard();
                    vm.stopLoader();
                },
                onError: function(response) {
                    var error = response.data;
                    vm.leaderboard.error = error;
                    vm.stopLoader();
                }
            };

            utilities.sendRequest(parameters);
            vm.startLeaderboard = function() {
                vm.stopLeaderboard();
                vm.poller = $interval(function() {
                    var parameters = {};
                    parameters.url = "jobs/" + "challenge_phase_split/" + vm.phaseSplitId + "/leaderboard/?page_size=1000";
                    parameters.method = 'GET';
                    parameters.data = {};
                    parameters.token = userKey;
                    parameters.callback = {
                        onSuccess: function(response) {
                            var details = response.data;
                            if (vm.leaderboard.count !== details.results.count) {
                                vm.showLeaderboardUpdate = true;
                            }
                        },
                        onError: function(response) {
                            var error = response.data;
                            utilities.storeData('emailError', error.detail);
                            $state.go('web.permission-denied');
                            vm.stopLoader();
                        }
                    };

                    utilities.sendRequest(parameters);
                }, 5000);
            };

        };
        vm.getResults = function(phaseId) {

            vm.stopFetchingSubmissions = function() {
                $interval.cancel(vm.poller);
            };
            vm.stopFetchingSubmissions();
            vm.isResult = true;
            vm.phaseId = phaseId;

            var all_phases = vm.phases.results;
            for (var i = 0; i < vm.phases.results.length; i++) {
                if (all_phases[i].id == phaseId) {
                    vm.currentPhaseLeaderboardPublic = all_phases[i].leaderboard_public;
                    break;
                }
            }

            parameters = {};
            parameters.url = "analytics/challenge/" + vm.challengeId + "/challenge_phase/"+ vm.phaseId + "/count";
            parameters.method = 'GET';
            parameters.data = {};
            parameters.token = userKey;
            parameters.callback = {
                onSuccess: function(response) {
                    var details = response.data;
                    vm.submissionCount = details.submissions_count_for_challenge_phase;
                },
                onError: function(response){
                    var error = response.data;
                    $rootScope.notify("error", error);
                }
            };
            utilities.sendRequest(parameters);

            // loader for exisiting teams
            vm.isExistLoader = true;
            vm.loaderTitle = '';
            vm.loaderContainer = angular.element('.exist-team-card');

            vm.startLoader("Loading Submissions");

            // get submissions of a particular challenge phase
            vm.isNext = '';
            vm.isPrev = '';
            vm.currentPage = '';
            vm.showPagination = false;

            var parameters = {};
            parameters.url = "jobs/challenge/" + vm.challengeId + "/challenge_phase/" + vm.phaseId + "/submission/";
            parameters.method = 'GET';
            parameters.data = {};
            parameters.token = userKey;
            parameters.callback = {
                onSuccess: function(response) {
                    var details = response.data;
                    vm.submissionResult = details;

                    for (var i = 0; i < details.results.length; i++) {
                        vm.submissionVisibility[details.results[i].id] = details.results[i].is_public;
                    }

                    vm.start();

                    if (vm.submissionResult.count === 0) {
                        vm.showPagination = false;
                        vm.paginationMsg = "No results found";
                    } else {

                        vm.showPagination = true;
                        vm.paginationMsg = "";
                    }

                    if (vm.submissionResult.next === null) {
                        vm.isNext = 'disabled';
                    } else {
                        vm.isNext = '';

                    }
                    if (vm.submissionResult.previous === null) {
                        vm.isPrev = 'disabled';
                    } else {
                        vm.isPrev = '';
                    }
                    if (vm.submissionResult.next !== null) {
                        vm.currentPage = vm.submissionResult.next.split('page=')[1] - 1;
                    } else {
                        vm.currentPage = 1;
                    }

                    vm.load = function(url) {
                        // loader for exisiting teams
                        vm.isExistLoader = true;
                        vm.loaderTitle = '';
                        vm.loaderContainer = angular.element('.exist-team-card');

                        vm.startLoader("Loading Submissions");
                        if (url !== null) {

                            //store the header data in a variable
                            var headers = {
                                'Authorization': "Token " + userKey
                            };

                            //Add headers with in your request
                            $http.get(url, { headers: headers }).then(function(response) {
                                // reinitialized data
                                var details = response.data;
                                vm.submissionResult = details;

                                // condition for pagination
                                if (vm.submissionResult.next === null) {
                                    vm.isNext = 'disabled';
                                    vm.currentPage = vm.submissionResult.count / 10;
                                } else {
                                    vm.isNext = '';
                                    vm.currentPage = parseInt(vm.submissionResult.next.split('page=')[1] - 1);
                                }

                                if (vm.submissionResult.previous === null) {
                                    vm.isPrev = 'disabled';
                                } else {
                                    vm.isPrev = '';
                                }
                                vm.stopLoader();
                            });
                        } else {
                            vm.stopLoader();
                        }
                    };
                    vm.stopLoader();
                },
                onError: function(response) {
                    var error = response.data;
                    utilities.storeData('emailError', error.detail);
                    $state.go('web.permission-denied');
                    vm.stopLoader();
                }
            };

            utilities.sendRequest(parameters);

            // long polling (5s) for leaderboard

            vm.start = function() {
                vm.stopFetchingSubmissions();
                vm.poller = $interval(function() {
                    var parameters = {};
                    parameters.url = "jobs/challenge/" + vm.challengeId + "/challenge_phase/" + vm.phaseId + "/submission/?page=" + Math.ceil(vm.currentPage);
                    parameters.method = 'GET';
                    parameters.data = {};
                    parameters.token = userKey;
                    parameters.callback = {
                        onSuccess: function(response) {
                            var details = response.data;

                            // Set the is_public flag corresponding to each submission
                            for (var i = 0; i < details.results.length; i++) {
                                vm.submissionVisibility[details.results[i].id] = details.results[i].is_public;
                            }

                            if (vm.submissionResult.results.length !== details.results.length) {
                                vm.showUpdate = true;
                            } else {
                                for (i = 0; i < details.results.length; i++) {
                                    if (details.results[i].status !== vm.submissionResult.results[i].status) {
                                        vm.showUpdate = true;
                                        break;
                                    }
                                }
                            }
                        },
                        onError: function(response) {
                            var error = response.data;
                            utilities.storeData('emailError', error.detail);
                            $state.go('web.permission-denied');
                            vm.stopLoader();
                        }
                    };

                    utilities.sendRequest(parameters);
                }, 5000);
            };
        };

        vm.refreshSubmissionData = function() {

            // get submissions of a particular challenge phase

            if (!vm.isResult) {

                vm.isNext = '';
                vm.isPrev = '';
                vm.currentPage = '';
                vm.showPagination = false;
            }

            vm.startLoader("Loading Submissions");
            vm.submissionResult = {};
            var parameters = {};

            parameters.url = "jobs/challenge/" + vm.challengeId + "/challenge_phase/" + vm.phaseId + "/submission/?page=" + Math.ceil(vm.currentPage);
            parameters.method = 'GET';
            parameters.data = {};
            parameters.token = userKey;
            parameters.callback = {
                onSuccess: function(response) {
                    var details = response.data;
                    vm.submissionResult = details;

                    if (vm.submissionResult.count === 0) {
                        vm.showPagination = false;
                        vm.paginationMsg = "No results found";
                    } else {

                        vm.showPagination = true;
                        vm.paginationMsg = "";
                    }

                    if (vm.submissionResult.next === null) {
                        vm.isNext = 'disabled';
                    } else {
                        vm.isNext = '';

                    }
                    if (vm.submissionResult.previous === null) {
                        vm.isPrev = 'disabled';
                    } else {
                        vm.isPrev = '';
                    }
                    if (vm.submissionResult.next !== null) {
                        vm.currentPage = vm.submissionResult.next.split('page=')[1] - 1;
                    } else {
                        vm.currentPage = 1;
                    }


                    // Set the is_public flag corresponding to each submission
                    for (var i = 0; i < details.results.length; i++) {
                        vm.submissionVisibility[details.results[i].id] = details.results[i].is_public;
                    }

                    vm.submissionResult = details;
                    vm.showUpdate = false;
                    vm.stopLoader();
                },
                onError: function() {
                    vm.stopLoader();
                }
            };

            utilities.sendRequest(parameters);
        };
        vm.refreshLeaderboard = function() {
            vm.startLoader("Loading Leaderboard Items");
            vm.leaderboard = {};
            var parameters = {};
            parameters.url = "jobs/" + "challenge_phase_split/" + vm.phaseSplitId + "/leaderboard/?page_size=1000";
            parameters.method = 'GET';
            parameters.data = {};
            parameters.token = userKey;
            parameters.callback = {
                onSuccess: function(response) {
                    var details = response.data;
                    vm.leaderboard = details.results;
                    vm.startLeaderboard();
                    vm.stopLoader();
                },
                onError: function(response) {
                    var error = response.data;
                    vm.leaderboard.error = error;
                    vm.stopLoader();
                }
            };

            utilities.sendRequest(parameters);
        };

        // function to create new team for participating in challenge
        vm.createNewTeam = function() {
            vm.isLoader = true;
            vm.loaderTitle = '';
            vm.newContainer = angular.element('.new-team-card');

            vm.startLoader("Loading Teams");

            var parameters = {};
            parameters.url = 'participants/participant_team';
            parameters.method = 'POST';
            parameters.data = {
                "team_name": vm.team.name
            };
            parameters.token = userKey;
            parameters.callback = {
                onSuccess: function() {
                    $rootScope.notify("success", "Team " + vm.team.name + " has been created successfully!");
                    vm.team.error = false;
                    vm.stopLoader();
                    vm.team.name = '';

                    vm.startLoader("Loading Teams");
                    var parameters = {};
                    parameters.url = 'participants/participant_team';
                    parameters.method = 'GET';
                    parameters.token = userKey;
                    parameters.callback = {
                        onSuccess: function(response) {
                            var status = response.status;
                            var details = response.data;
                            if (status == 200) {
                                vm.existTeam = details;
                                vm.showPagination = true;
                                vm.paginationMsg = '';


                                // condition for pagination
                                if (vm.existTeam.next === null) {
                                    vm.isNext = 'disabled';
                                    vm.currentPage = 1;
                                } else {
                                    vm.isNext = '';
                                    vm.currentPage = vm.existTeam.next.split('page=')[1] - 1;
                                }

                                if (vm.existTeam.previous === null) {
                                    vm.isPrev = 'disabled';
                                } else {
                                    vm.isPrev = '';
                                }


                                vm.stopLoader();
                            }
                        },
                        onError: function() {
                            vm.stopLoader();
                        }
                    };
                    utilities.sendRequest(parameters);
                },
                onError: function(response) {
                    var error = response.data;
                    vm.team.error = error.team_name[0];
                    vm.stopLoader();
                    $rootScope.notify("error", "New team couldn't be created.");
                }
            };

            utilities.sendRequest(parameters);
        };

        vm.getAllSubmissionResults = function(phaseId) {

            vm.stopFetchingSubmissions = function() {
                $interval.cancel(vm.poller);
            };

            vm.stopFetchingSubmissions();
            vm.isResult = true;
            vm.phaseId = phaseId;

            // loader for loading submissions.
            vm.startLoader =  loaderService.startLoader;
            vm.startLoader("Loading Submissions");

            // get submissions of all the challenge phases
            vm.isNext = '';
            vm.isPrev = '';
            vm.currentPage = '';
            vm.showPagination = false;

            var parameters = {};
            parameters.url = "challenges/" + vm.challengeId + "/challenge_phase/" + vm.phaseId + "/submissions";
            parameters.method = 'GET';
            parameters.data = {};
            parameters.token = userKey;
            parameters.callback = {
                onSuccess: function(response) {
                    var details = response.data;
                    vm.submissionResult = details;

                    if (vm.submissionResult.count === 0) {
                        vm.showPagination = false;
                        vm.paginationMsg = "No results found";
                    } else {

                        vm.showPagination = true;
                        vm.paginationMsg = "";
                    }

                    if (vm.submissionResult.next === null) {
                        vm.isNext = 'disabled';
                    } else {
                        vm.isNext = '';

                    }
                    if (vm.submissionResult.previous === null) {
                        vm.isPrev = 'disabled';
                    } else {
                        vm.isPrev = '';
                    }
                    if (vm.submissionResult.next !== null) {
                        vm.currentPage = vm.submissionResult.next.split('page=')[1] - 1;
                    } else {
                        vm.currentPage = 1;
                    }

                    vm.load = function(url) {
                        // loader for loading submissions
                        vm.startLoader =  loaderService.startLoader;
                        vm.startLoader("Loading Submissions");
                        if (url !== null) {

                            //store the header data in a variable
                            var headers = {
                                'Authorization': "Token " + userKey
                            };

                            //Add headers with in your request
                            $http.get(url, { headers: headers }).then(function(response) {
                                // reinitialized data
                                var details = response.data;
                                vm.submissionResult = details;

                                // condition for pagination
                                if (vm.submissionResult.next === null) {
                                    vm.isNext = 'disabled';
                                    vm.currentPage = vm.submissionResult.count / 10;
                                } else {
                                    vm.isNext = '';
                                    vm.currentPage = parseInt(vm.submissionResult.next.split('page=')[1] - 1);
                                }

                                if (vm.submissionResult.previous === null) {
                                    vm.isPrev = 'disabled';
                                } else {
                                    vm.isPrev = '';
                                }
                                vm.stopLoader();
                            });
                        } else {
                            vm.stopLoader();
                        }
                    };
                    vm.stopLoader();
                },
                onError: function(response) {
                    var error = response.data;
                    utilities.storeData('emailError', error.detail);
                    $state.go('web.permission-denied');
                    vm.stopLoader();
                }
            };
            utilities.sendRequest(parameters);
        };

        vm.changeSubmissionVisibility = function(submission_id) {
            var parameters = {};
            parameters.url = "jobs/challenge/" + vm.challengeId + "/challenge_phase/" + vm.phaseId + "/submission/" + submission_id;
            parameters.method = 'PATCH';
            parameters.data = {
                "is_public": vm.submissionVisibility[submission_id]
            };
            parameters.token = userKey;
            parameters.callback = {
                onSuccess: function() {},
                onError: function() {}
            };

            utilities.sendRequest(parameters);
        };

        vm.showRemainingSubmissions = function() {
            var parameters = {};
            vm.remainingSubmissions = {};
            vm.remainingTime = {};
            vm.showClock = false;
            vm.showSubmissionNumbers = false;
            parameters.url = "jobs/"+ vm.challengeId + "/phases/"+ vm.phaseId + "/remaining_submissions";
            parameters.method = 'GET';
            parameters.token = userKey;
            parameters.callback = {
                onSuccess: function(response) {
                    var status = response.status;
                    var details = response.data;
                    if (status === 200) {
                        if (details.remaining_submissions_today_count > 0) {
                            vm.remainingSubmissions = details;
                            vm.showSubmissionNumbers = true;
                        } else {
                            vm.message = details;
                            vm.showClock = true;
                            vm.countDownTimer = function() {
                                vm.remainingTime = vm.message.remaining_time;
                                vm.days = Math.floor(vm.remainingTime/24/60/60);
                                vm.hoursLeft = Math.floor((vm.remainingTime) - (vm.days*86400));
                                vm.hours = Math.floor(vm.hoursLeft/3600);
                                vm.minutesLeft = Math.floor((vm.hoursLeft) - (vm.hours*3600));
                                vm.minutes = Math.floor(vm.minutesLeft/60);
                                vm.remainingSeconds = Math.floor(vm.remainingTime % 60);
                                if (vm.remainingSeconds < 10) {
                                    vm.remainingSeconds = "0" + vm.remainingSeconds;
                                }
                                if (vm.remainingTime === 0) {
                                    vm.showSubmissionNumbers = true;
                                }
                                else {
                                    vm.remainingSeconds--;
                                }
                            };
                            setInterval(function() {
                                $rootScope.$apply(vm.countDownTimer);
                                }, 1000);
                                vm.countDownTimer();
                        }
                    }
                },
                onError: function() {
                    vm.stopLoader();
                    $rootScope.notify("error", "Some error occured. Please try again.");
                }
            };
            utilities.sendRequest(parameters);
        };

        vm.fileTypes = [{'name': 'csv'}];

        vm.downloadChallengeSubmissions = function() {
            if(vm.phaseId) {
                var parameters = {};
                parameters.url = "challenges/"+ vm.challengeId + "/phase/" + vm.phaseId + "/download_all_submissions/" + vm.fileSelected + "/";
                parameters.method = "GET";
                parameters.token = userKey;
                parameters.callback = {
                    onSuccess: function(response) {
                        var details = response.data;
                        var anchor = angular.element('<a/>');
                        anchor.attr({
                        href: 'data:attachment/csv;charset=utf-8,' + encodeURI(details),
                        download: 'all_submissions.csv'
                        })[0].click();
                    },
                    onError: function(response) {
                        var details = response.data;
                        $rootScope.notify('error', details.error);
                    }
                };
                utilities.sendRequest(parameters);
        }else {
            $rootScope.notify("error", "Please select a challenge phase!");
        }
        };

        vm.showMdDialog = function(ev, submissionId) {
            for (var i=0;i<vm.submissionResult.count;i++){
                if (vm.submissionResult.results[i].id === submissionId) {
                    vm.submissionMetaData = vm.submissionResult.results[i];
                    break;
                }
            }
            vm.method_name = vm.submissionMetaData.method_name;
            vm.method_description = vm.submissionMetaData.method_description;
            vm.project_url = vm.submissionMetaData.project_url;
            vm.publication_url = vm.submissionMetaData.publication_url;
            vm.submissionId = submissionId;

            $mdDialog.show({
                scope: $scope,
                preserveScope: true,
                targetEvent: ev,
                templateUrl: 'dist/views/web/challenge/update-submission-metadata.html'
            });
        };

        vm.updateSubmissionMetaData = function(updateSubmissionMetaDataForm) {
            if(updateSubmissionMetaDataForm){
                var parameters = {};
                parameters.url = "jobs/challenge/" + vm.challengeId + "/challenge_phase/" + vm.phaseId + "/submission/" + vm.submissionId;
                parameters.method = 'PATCH';
                parameters.data = {
                    "method_name": vm.method_name,
                    "method_description": vm.method_description,
                    "project_url": vm.project_url,
                    "publication_url": vm.publication_url
                };
                parameters.token = userKey;
                parameters.callback = {
                    onSuccess: function(response) {
                        var status = response.status;
                        if (status === 200){
                            $mdDialog.hide();
                            $rootScope.notify("success", "The data is successfully updated!");
                        }
                    },
                    onError: function(response) {
                        $mdDialog.hide();
                        var error = response.data;
                        $rootScope.notify("error", error);
                    }
                };

                utilities.sendRequest(parameters);
            }
            else{
              $mdDialog.hide();
            }
        };

        // Get the stars count and user specific starred or unstarred
        parameters = {};
        parameters.url = "challenges/"+ vm.challengeId + "/";
        parameters.method = 'GET';
        parameters.token = userKey;
        parameters.callback = {
            onSuccess: function(response) {
                var details = response.data;
                vm.count = details['count'] || 0;
                vm.is_starred = details['is_starred'];
                if (details['is_starred'] === false){
                    vm.data = 'Star';
                }
                else{
                    vm.data = 'Unstar';
                }
            },
            onError: function() {}
        };
        utilities.sendRequest(parameters);

        vm.starChallenge = function() {
            var parameters = {};
            parameters.url = "challenges/"+ vm.challengeId + "/";
            parameters.method = 'POST';
            parameters.data = {};
            parameters.token = userKey;
            parameters.callback = {
                onSuccess: function(response) {
                    var details = response.data;
                    vm.count = details['count'];
                    vm.is_starred = details['is_starred'];
                    if (details.is_starred === true) {
                        vm.data = 'Unstar';
                    } else{
                        vm.data = 'Star';
                    }
                },
                onError: function(response) {
                    var error = response.data;
                    $rootScope.notify("error", error);
                }
            };
            utilities.sendRequest(parameters);
        };

// Edit challenge overview
        vm.overviewDialog = function(ev) {
            vm.tempDesc = vm.page.description;
            $mdDialog.show({
                scope: $scope,
                preserveScope: true,
                targetEvent: ev,
                templateUrl: 'dist/views/web/challenge/edit-challenge/edit-challenge-overview.html',
                escapeToClose: false
            });
        };

        vm.editChallengeOverview = function(editChallengeOverviewForm) {
            if(editChallengeOverviewForm){
                var parameters = {};
                var challengeHostList = utilities.getData("challengeCreator");
                for (var challenge in challengeHostList) {
                    if (challenge==vm.challengeId) {
                            vm.challengeHostId = challengeHostList[challenge];
                            break;
                        }
                    }
                parameters.url = "challenges/challenge_host_team/" + vm.challengeHostId + "/challenge/" + vm.challengeId;
                parameters.method = 'PATCH';
                parameters.data = {
                    "description": vm.page.description

                };
                parameters.token = userKey;
                parameters.callback = {
                    onSuccess: function(response) {
                        var status = response.status;
                        if (status === 200){
                            $mdDialog.hide();
                            $rootScope.notify("success", "The description is successfully updated!");
                        }
                    },
                    onError: function(response) {
                        $mdDialog.hide();
                        vm.page.description = vm.tempDesc;
                        var error = response.data;
                        $rootScope.notify("error", error);
                    }
                };

                utilities.sendRequest(parameters);
            } else {
                vm.page.description = vm.tempDesc;
                $mdDialog.hide();
            }
        };

// Edit submission guidelines
        vm.submissionGuidelinesDialog = function(ev) {
            vm.tempSubmissionGuidelines = vm.page.submission_guidelines;
            console.log("ABCCCCCCCCCCCC");
            console.log(vm.tempTermsAndConditions);
            $mdDialog.show({
                scope: $scope,
                preserveScope: true,
                targetEvent: ev,
                templateUrl: 'dist/views/web/challenge/edit-challenge/edit-challenge-submission-guidelines.html',
                escapeToClose: false
            });
        };

        vm.editSubmissionGuideline = function(editSubmissionGuidelinesForm) {
            if(editSubmissionGuidelinesForm){
                var parameters = {};
                var challengeHostList = utilities.getData("challengeCreator");
                for (var challenge in challengeHostList) {
                    if (challenge==vm.challengeId) {
                            vm.challengeHostId = challengeHostList[challenge];
                            break;
                        }
                    }
                console.log("BLANK"+vm.page.submission_guidelines);
                parameters.url = "challenges/challenge_host_team/" + vm.challengeHostId + "/challenge/" + vm.challengeId;
                parameters.method = 'PATCH';
                parameters.data = {
                    "submission_guidelines": vm.page.submission_guidelines

                };
                parameters.token = userKey;
                parameters.callback = {
                    onSuccess: function(response) {
                        var status = response.status;
                        if (status === 200){
                            $mdDialog.hide();
                            $rootScope.notify("success", "The submission guidelines is successfully updated!");
                        }
                    },
                    onError: function(response) {
                        $mdDialog.hide();
                        vm.page.submission_guidelines = vm.tempSubmissionGuidelines;
                        var error = response.data;
                        $rootScope.notify("error", error);
                    }
                };

                utilities.sendRequest(parameters);
            } else {
                vm.page.submission_guidelines = vm.tempSubmissionGuidelines;
                $mdDialog.hide();
            }
        };

// Edit Evaluation Criteria
        vm.evaluationCriteriaDialog = function(ev) {
            vm.tempEvaluationCriteria = vm.page.evaluation_details;
            $mdDialog.show({
                scope: $scope,
                preserveScope: true,
                targetEvent: ev,
                templateUrl: 'dist/views/web/challenge/edit-challenge/edit-challenge-evaluation-criteria.html',
                escapeToClose: false
            });
        };

        vm.editEvaluationCriteria = function(editEvaluationCriteriaForm) {
            if(editEvaluationCriteriaForm){
                var parameters = {};
                var challengeHostList = utilities.getData("challengeCreator");
                for (var challenge in challengeHostList) {
                    if (challenge==vm.challengeId) {
                            vm.challengeHostId = challengeHostList[challenge];
                            break;
                        }
                    }
                parameters.url = "challenges/challenge_host_team/" + vm.challengeHostId + "/challenge/" + vm.challengeId;
                parameters.method = 'PATCH';
                parameters.data = {
                    "evaluation_details": vm.page.evaluation_details
                };
                parameters.token = userKey;
                parameters.callback = {
                    onSuccess: function(response) {
                        var status = response.status;
                        if (status === 200){
                            $mdDialog.hide();
                            $rootScope.notify("success", "The evaluation details is successfully updated!");
                        }
                    },
                    onError: function(response) {
                        $mdDialog.hide();
                        vm.page.evaluation_details = vm.tempEvaluationCriteria;
                        var error = response.data;
                        $rootScope.notify("error", error);
                    }
                };

                utilities.sendRequest(parameters);

            } else {
                vm.page.evaluation_details = vm.tempEvaluationCriteria;
                $mdDialog.hide();
            }
        };


// Edit Evaluation Script
        vm.evaluationScriptDialog = function(ev) {
            $mdDialog.show({
                scope: $scope,
                preserveScope: true,
                targetEvent: ev,
                templateUrl: 'dist/views/web/challenge/edit-challenge/edit-challenge-evaluation-script.html',
                escapeToClose: false
            });
        };

        vm.editEvalScript = function(editEvaluationCriteriaForm) {
            if(editEvaluationCriteriaForm){
                var parameters = {};
                var formData = new FormData();
                formData.append("evaluation_script", vm.editEvaluationScript);
                var challengeHostList = utilities.getData("challengeCreator");
                for (var challenge in challengeHostList) {
                    if (challenge==vm.challengeId) {
                            vm.challengeHostId = challengeHostList[challenge];
                            break;
                        }
                    }
                parameters.url = "challenges/challenge_host_team/" + vm.challengeHostId + "/challenge/" + vm.challengeId;
                parameters.method = 'PATCH';
                parameters.data = formData;
                parameters.token = userKey;
                parameters.callback = {
                    onSuccess: function(response) {
                        var status = response.status;
                        if (status === 200){
                            $mdDialog.hide();
                            $rootScope.notify("success", "The evaluation script is successfully updated!");
                        }
                    },
                    onError: function(response) {
                        $mdDialog.hide();
                        vm.page.evaluation_details = vm.tempEvaluationCriteria;
                        var error = response.data;
                        $rootScope.notify("error", error);
                    }
                };

                utilities.sendRequest(parameters, 'header', 'upload');

            } else {
                vm.page.evaluation_details = vm.tempEvaluationCriteria;
                $mdDialog.hide();
            }
        };


// Edit Terms and Conditions
        vm.termsAndConditionsDialog = function(ev) {
            vm.tempTermsAndConditions = vm.page.terms_and_conditions;
            $mdDialog.show({
                scope: $scope,
                preserveScope: true,
                targetEvent: ev,
                templateUrl: 'dist/views/web/challenge/edit-challenge/edit-challenge-terms-and-conditions.html',
                escapeToClose: false
            });
        };

        vm.editTermsAndConditions = function(editTermsAndConditionsForm) {
            if(editTermsAndConditionsForm){
                var parameters = {};
                var challengeHostList = utilities.getData("challengeCreator");
                for (var challenge in challengeHostList) {
                    if (challenge==vm.challengeId) {
                            vm.challengeHostId = challengeHostList[challenge];
                            break;
                        }
                    }
                parameters.url = "challenges/challenge_host_team/" + vm.challengeHostId + "/challenge/" + vm.challengeId;
                parameters.method = 'PATCH';
                parameters.data = {
                    "terms_and_conditions": vm.page.terms_and_conditions
                };
                parameters.token = userKey;
                parameters.callback = {
                    onSuccess: function(response) {
                        var status = response.status;
                        if (status === 200) {
                            $mdDialog.hide();
                            $rootScope.notify("success", "The terms and conditions are successfully updated!");
                        }
                    },
                    onError: function(response) {
                        $mdDialog.hide();
                        vm.page.terms_and_conditions = vm.tempTermsAndConditions;
                        var error = response.data;
                        $rootScope.notify("error", error);
                    }
                };
                utilities.sendRequest(parameters);
            } else {
                vm.page.terms_and_conditions = vm.tempTermsAndConditions;
                $mdDialog.hide();
            }
        };

// Edit Challenge Title
        vm.challengeTitleDialog = function(ev) {
            vm.tempChallengeTitle = vm.page.title;
            $mdDialog.show({
                scope: $scope,
                preserveScope: true,
                targetEvent: ev,
                templateUrl: 'dist/views/web/challenge/edit-challenge/edit-challenge-title.html',
                escapeToClose: false
            });
        };

        vm.editChallengeTitle = function(editChallengeTitleForm) {
            if(editChallengeTitleForm){
                var parameters = {};
                var challengeHostList = utilities.getData("challengeCreator");
                for (var challenge in challengeHostList) {
                    if (challenge==vm.challengeId) {
                            vm.challengeHostId = challengeHostList[challenge];
                            break;
                        }
                    }
                parameters.url = "challenges/challenge_host_team/" + vm.challengeHostId + "/challenge/" + vm.challengeId;
                parameters.method = 'PATCH';
                parameters.data = {
                    "title": vm.page.title
                };
                parameters.token = userKey;
                parameters.callback = {
                    onSuccess: function(response) {
                        var status = response.status;
                        if (status === 200) {
                            $mdDialog.hide();
                            $rootScope.notify("success", "The challenge title is  successfully updated!");
                        }
                    },
                    onError: function(response) {
                        $mdDialog.hide();
                        vm.page.title = vm.tempChallengeTitle;
                        var error = response.data;
                        $rootScope.notify("error", error);
                    }
                };
                utilities.sendRequest(parameters);
            } else {
                vm.page.title = vm.tempChallengeTitle;
                $mdDialog.hide();
            }
        };

        $scope.$on('$destroy', function() {
            vm.stopFetchingSubmissions();
            vm.stopLeaderboard();
        });

        $rootScope.$on('$stateChangeStart', function() {
            vm.phase = {};
            vm.isResult = false;
            vm.stopFetchingSubmissions();
            vm.stopLeaderboard();
        });
    }

})();

// Invoking IIFE for teams
(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('ChallengeHostTeamsCtrl', ChallengeHostTeamsCtrl);

    ChallengeHostTeamsCtrl.$inject = ['utilities', 'loaderService', '$state', '$http', '$rootScope', '$mdDialog'];

    function ChallengeHostTeamsCtrl(utilities, loaderService, $state, $http, $rootScope, $mdDialog) {
        var vm = this;
        // console.log(vm.teamId)
        var userKey = utilities.getData('userKey');

        utilities.showLoader();

        // default variables/objects
        vm.team = {};
        vm.teamId = null;
        vm.existTeam = {};
        vm.currentPage = '';
        vm.isNext = '';
        vm.isPrev = '';
        vm.team.error = false;
        vm.showPagination = false;
        vm.hostTeamId = null;
        vm.challengeHostTeamId = null;

        // loader for existng teams// loader for exisiting teams
        vm.isExistLoader = false;
        vm.loaderTitle = '';
        vm.loaderContainer = angular.element('.exist-team-card');
         // show loader
        vm.startLoader = loaderService.startLoader;

        // stop loader
        vm.stopLoader = loaderService.stopLoader;


        vm.activateCollapsible = function() {
            angular.element('.collapsible').collapsible();
        };

        var parameters = {};
        parameters.url = 'hosts/challenge_host_team/';
        parameters.method = 'GET';
        parameters.token = userKey;
        parameters.callback = {
            onSuccess: function(response) {
                var status = response.status;
                var details = response.data;
                if (status == 200) {
                    vm.existTeam = details;

                    if (vm.existTeam.count === 0) {
                        vm.showPagination = false;
                        vm.paginationMsg = "No team exists for now, start by creating a new team!";
                    } else {
                        vm.activateCollapsible();
                        vm.showPagination = true;
                        vm.paginationMsg = "";
                    }

                    // clear error msg from storage
                    utilities.deleteData('emailError');

                    // condition for pagination
                    if (vm.existTeam.next === null) {
                        vm.isNext = 'disabled';
                    } else {
                        vm.isNext = '';
                    }

                    if (vm.existTeam.previous === null) {
                        vm.isPrev = 'disabled';
                    } else {
                        vm.isPrev = '';
                    }
                    if (vm.existTeam.next !== null) {
                        vm.currentPage = vm.existTeam.next.split('page=')[1] - 1;
                    } else {
                        vm.currentPage = 1;
                    }

                    // to load data with pagination
                    vm.load = function(url) {
                        // loader for exisiting teams
                        vm.isExistLoader = true;
                        vm.loaderTitle = '';
                        vm.loaderContainer = angular.element('.exist-team-card');

                        vm.startLoader("Loading Teams");
                        if (url !== null) {

                            //store the header data in a variable
                            var headers = {
                                'Authorization': "Token " + userKey
                            };

                            //Add headers with in your request
                            $http.get(url, { headers: headers }).then(function(response) {
                                // reinitialized data
                                var details = response.data;
                                vm.existTeam = details;

                                // condition for pagination
                                if (vm.existTeam.next === null) {
                                    vm.isNext = 'disabled';
                                    vm.currentPage = vm.existTeam.count / 10;
                                } else {
                                    vm.isNext = '';
                                    vm.currentPage = parseInt(vm.existTeam.next.split('page=')[1] - 1);
                                }

                                if (vm.existTeam.previous === null) {
                                    vm.isPrev = 'disabled';
                                } else {
                                    vm.isPrev = '';
                                }
                                vm.stopLoader();
                            });
                        } else {
                            vm.stopLoader();
                        }
                    };

                }
                utilities.hideLoader();
            },
            onError: function(response) {
                var error = response.data;
                utilities.storeData('emailError', error.detail);
                $state.go('web.permission-denied');
                utilities.hideLoader();
            }
        };

        utilities.sendRequest(parameters);

        // function to create new team
        vm.createNewTeam = function() {
            vm.isLoader = true;
            vm.loaderTitle = '';
            vm.newContainer = angular.element('.new-team-card');

            // show loader
            vm.startLoader = function(msg) {
                vm.isLoader = true;
                vm.loaderTitle = msg;
                vm.newContainer.addClass('low-screen');
            };

            // stop loader
            vm.stopLoader = function() {
                vm.isLoader = false;
                vm.loaderTitle = '';
                vm.newContainer.removeClass('low-screen');
            };

            vm.startLoader("Loading Teams");

            var parameters = {};
            parameters.url = 'hosts/create_challenge_host_team';
            parameters.method = 'POST';
            parameters.data = {
                "team_name": vm.team.name
            };
            parameters.token = userKey;
            parameters.callback = {
                onSuccess: function(response) {
                    $rootScope.notify("success", "New team- '" + vm.team.name + "' has been created");
                    var details = response.data;
                    vm.teamId = details.id;
                    vm.team.error = false;
                    vm.team.name = '';
                    vm.stopLoader();

                    vm.startLoader("Loading Teams");
                    var parameters = {};
                    parameters.url = 'hosts/challenge_host_team/';
                    parameters.method = 'GET';
                    parameters.token = userKey;
                    parameters.callback = {
                        onSuccess: function(response) {
                            var status = response.status;
                            var details = response.data;
                            if (status == 200) {
                                vm.existTeam = details;
                                vm.showPagination = true;
                                vm.paginationMsg = '';


                                // condition for pagination
                                if (vm.existTeam.next === null) {
                                    vm.isNext = 'disabled';
                                    vm.currentPage = 1;
                                } else {
                                    vm.isNext = '';
                                    vm.currentPage = vm.existTeam.next.split('page=')[1] - 1;
                                }

                                if (vm.existTeam.previous === null) {
                                    vm.isPrev = 'disabled';
                                } else {
                                    vm.isPrev = '';
                                }


                                vm.stopLoader();
                            }
                        },
                        onError: function() {
                            vm.stopLoader();
                        }
                    };
                    utilities.sendRequest(parameters);

                },
                onError: function(response) {
                    var error = response.data;
                    vm.team.error = error.team_name[0];
                    vm.stopLoader();
                    $rootScope.notify("error", "New team couldn't be created.");
                }
            };

            utilities.sendRequest(parameters);

        };

        vm.confirmDelete = function(ev, hostTeamId) {
            ev.stopPropagation();
            // Appending dialog to document.body to cover sidenav in docs app
            var confirm = $mdDialog.confirm()
                .title('Would you like to remove yourself?')
                .textContent('Note: This action will remove you from the team.')
                .ariaLabel('Lucky day')
                .targetEvent(ev)
                .ok('Yes')
                .cancel("No");

            $mdDialog.show(confirm).then(function() {
                vm.startLoader();
                var parameters = {};
                parameters.url = 'hosts/remove_self_from_challenge_host/' + hostTeamId;
                parameters.method = 'DELETE';
                parameters.data = {};
                parameters.token = userKey;
                parameters.callback = {
                    onSuccess: function() {
                        vm.team.error = false;
                        $rootScope.notify("info", "You have removed yourself successfully");

                        var parameters = {};
                        parameters.url = 'hosts/challenge_host_team/';
                        parameters.method = 'GET';
                        parameters.token = userKey;
                        parameters.callback = {
                            onSuccess: function(response) {
                                var status = response.status;
                                var details = response.data;
                                if (status == 200) {
                                    vm.existTeam = details;


                                    // condition for pagination
                                    if (vm.existTeam.next === null) {
                                        vm.isNext = 'disabled';
                                        vm.currentPage = vm.existTeam.count / 10;
                                    } else {
                                        vm.isNext = '';
                                        vm.currentPage = parseInt(vm.existTeam.next.split('page=')[1] - 1);
                                    }

                                    if (vm.existTeam.previous === null) {
                                        vm.isPrev = 'disabled';
                                    } else {
                                        vm.isPrev = '';
                                    }


                                    if (vm.existTeam.count === 0) {

                                        vm.showPagination = false;
                                        vm.paginationMsg = "No team exists for now, start by creating a new team!";
                                    } else {
                                        vm.showPagination = true;
                                        vm.paginationMsg = "";
                                    }
                                }

                                vm.stopLoader();
                            }
                        };
                        utilities.sendRequest(parameters);
                    },
                    onError: function() {
                        vm.stopLoader();
                        $rootScope.notify("error", "Couldn't remove you from the challenge");
                    }
                };

                utilities.sendRequest(parameters);

            }, function() {});
        };

        vm.inviteOthers = function(ev, hostTeamId) {
            ev.stopPropagation();
            // Appending dialog to document.body 
            var confirm = $mdDialog.prompt()
                .title('Invite others to this Team')
                .textContent('Enter the email address of the person')
                .placeholder('email')
                .ariaLabel('')
                .targetEvent(ev)
                .ok('Send Invite')
                .cancel('Cancel');

            $mdDialog.show(confirm).then(function(result) {

                var parameters = {};
                parameters.url = 'hosts/challenge_host_teams/' + hostTeamId + '/invite';
                parameters.method = 'POST';
                parameters.data = {
                    "email": result
                };
                parameters.token = userKey;
                parameters.callback = {
                    onSuccess: function() {
                        $rootScope.notify("success", parameters.data.email + " has been invited successfully");
                    },
                    onError: function() {
                        $rootScope.notify("error", "Couldn't invite " + parameters.data.email + ". Please try again.");
                    }
                };

                utilities.sendRequest(parameters);
            });
        };

    vm.storeChallengeHostTeamId = function() {

        utilities.storeData('challengeHostTeamId', vm.challengeHostTeamId);
        $state.go('web.challenge-create');
    };

    }

})();

// Invoking IIFE for challenge page
(function() {

    'use strict';
    angular
        .module('evalai')
        .controller('ChallengeListCtrl', ChallengeListCtrl);

    ChallengeListCtrl.$inject = ['utilities'];

    function ChallengeListCtrl(utilities) {
        var vm = this;
        var userKey = utilities.getData('userKey');

        utilities.showLoader();

        vm.currentList = {};
        vm.upcomingList = {};
        vm.pastList = {};

        vm.noneCurrentChallenge = false;
        vm.noneUpcomingChallenge = false;
        vm.nonePastChallenge = false;

        // calls for ongoing challneges
        vm.challengeCreator = {};
        var parameters = {};
        parameters.url = 'challenges/challenge/present';
        parameters.method = 'GET';
        parameters.token = userKey;

        parameters.callback = {
            onSuccess: function(response) {
                var data = response.data;
                vm.currentList = data.results;

                if (vm.currentList.length === 0) {
                    vm.noneCurrentChallenge = true;
                } else {
                    vm.noneCurrentChallenge = false;
                }

                for (var i in vm.currentList) {

                    var descLength = vm.currentList[i].description.length;
                    if (descLength >= 50) {
                        vm.currentList[i].isLarge = "...";
                    } else {
                        vm.currentList[i].isLarge = "";
                    }

                    var id = vm.currentList[i].id;              
                    vm.challengeCreator[id]= vm.currentList[i].creator.id;
                    utilities.storeData("challengeCreator", vm.challengeCreator);
                }

                // dependent api
                // calls for upcoming challneges
                var parameters = {};
                parameters.url = 'challenges/challenge/future';
                parameters.method = 'GET';
                parameters.token = userKey;

                parameters.callback = {
                    onSuccess: function(response) {
                        var data = response.data;
                        vm.upcomingList = data.results;

                        if (vm.upcomingList.length === 0) {
                            vm.noneUpcomingChallenge = true;
                        } else {
                            vm.noneUpcomingChallenge = false;
                        }

                        for (var i in vm.upcomingList) {

                            var descLength = vm.upcomingList[i].description.length;

                            if (descLength >= 50) {
                                vm.upcomingList[i].isLarge = "...";
                            } else {
                                vm.upcomingList[i].isLarge = "";
                            }

                            var id = vm.upcomingList[i].id;              
                            vm.challengeCreator[id] = vm.upcomingList[i].creator.id;
                            utilities.storeData("challengeCreator", vm.challengeCreator);
                        }

                        // dependent api
                        // calls for upcoming challneges
                        var parameters = {};
                        parameters.url = 'challenges/challenge/past';
                        parameters.method = 'GET';
                        parameters.token = userKey;

                        parameters.callback = {
                            onSuccess: function(response) {
                                var data = response.data;
                                vm.pastList = data.results;

                                if (vm.pastList.length === 0) {
                                    vm.nonePastChallenge = true;
                                } else {
                                    vm.nonePastChallenge = false;
                                }


                                for (var i in vm.pastList) {


                                    var descLength = vm.pastList[i].description.length;
                                    if (descLength >= 50) {
                                        vm.pastList[i].isLarge = "...";
                                    } else {
                                        vm.pastList[i].isLarge = "";
                                    }
                                    var id = vm.pastList[i].id;              
                                    vm.challengeCreator[id]= vm.pastList[i].creator.id;
                                    utilities.storeData("challengeCreator", vm.challengeCreator);
                                }

                                utilities.hideLoader();

                            },
                            onError: function() {
                                utilities.hideLoader();
                            }
                        };

                        utilities.sendRequest(parameters);

                    },
                    onError: function() {
                        utilities.hideLoader();
                    }
                };

                utilities.sendRequest(parameters);

            },
            onError: function() {

                utilities.hideLoader();
            }
        };

        utilities.sendRequest(parameters);



        // utilities.showLoader();
    }

})();

// Invoking IIFE for teams
(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('ChangePwdCtrl', ChangePwdCtrl);

    ChangePwdCtrl.$inject = ['utilities', '$state', '$http', '$rootScope'];

    function ChangePwdCtrl(utilities, $state, $http, $rootScope) {
        var vm = this;
        var userKey = utilities.getData('userKey');
        vm.wrnMsg = {};
        vm.isValid = {};
        vm.user = {};
        vm.isFormError = false;

        vm.changepassContainer = angular.element('.change-passowrd-card');

        vm.startLoader = function(msg) {
            $rootScope.isLoader = true;
            $rootScope.loaderTitle = msg;
            vm.changepassContainer.addClass('low-screen');
        };

        // stop loader
        vm.stopLoader = function() {
            $rootScope.isLoader = false;
            $rootScope.loaderTitle = '';
            vm.changepassContainer.removeClass('low-screen');
        };
        // function to change password
        vm.changePassword = function(resetconfirmFormValid) {
          if(resetconfirmFormValid){


            vm.startLoader("Changing Your Password");
            var parameters = {};
            parameters.url = 'auth/password/change/';
            parameters.method = 'POST';
            parameters.data = {
                "old_password": vm.user.old_password,
                "new_password1": vm.user.new_password1,
                "new_password2": vm.user.new_password2,
                "uid": $state.params.user_id,
            };
            parameters.token = userKey;
                parameters.callback = {
                    onSuccess: function() {
                        vm.user.error = false;
                        $rootScope.notify("success", "Your password has been changed successfully!");
                        vm.stopLoader();
                        // navigate to challenge page
                        // $state.go('web.challenge-page.overview');
                    },
                    onError: function(response) {
                        vm.user.error = "Failed";
                        vm.isFormError = true;
                        var oldpassword_valid ,password1_valid, password2_valid;
                        try {
                            oldpassword_valid = typeof(response.data.old_password) !== 'undefined' ? true : false;
                            password1_valid = typeof(response.data.new_password1) !== 'undefined' ? true : false;
                            password2_valid = typeof(response.data.new_password2) !== 'undefined' ? true : false;
                            if (oldpassword_valid) {
                                vm.FormError = Object.values(response.data.old_password).join(" ");
                            }else if (password1_valid) {
                                vm.FormError = Object.values(response.data.new_password1).join(" ");
                            } else if (password2_valid) {
                                vm.FormError = Object.values(response.data.new_password2).join(" ");
                            }
                        } catch (error) { 
                            vm.FormError = "Something went wrong! Please refresh the page and try again.";
                        }
                        vm.stopLoader();
                    }
                };

                utilities.sendRequest(parameters);

            }else {
              vm.stopLoader();
            }
        };
    }

})();

// Invoking IIFE for contact us

(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('contactUsCtrl', contactUsCtrl);

    contactUsCtrl.$inject = ['utilities', 'loaderService', '$state', '$http', '$rootScope'];

    function contactUsCtrl(utilities, loaderService, $state, $http, $rootScope) {
        var vm = this;
        var userKey = utilities.getData('userKey');
        vm.wrnMsg = {};
        vm.isValid = {};
        vm.user = {};
        vm.isFormError = false;

        // start loader
        vm.startLoader =  loaderService.startLoader;

        // stop loader
        vm.stopLoader = loaderService.stopLoader;

        // To get the previous profile data
        var parameters = {};
        parameters.url = 'web/contact/';
        parameters.method = 'GET';
        parameters.token = userKey;
        parameters.callback = {
            onSuccess: function(response) {
                var status = response.status;
                var result = response.data;
                if (status == 200) {
                    vm.user = result;
                    vm.isDisabled = true;
                }
            },
            onError: function() {
            }
        };

        utilities.sendRequest(parameters);

        // function to post data in contact us form
        vm.contactUs = function(resetconfirmFormValid) {
            if (resetconfirmFormValid) {

                var parameters = {};
                vm.isDisabled = false;
                parameters.url = 'web/contact/';
                parameters.method = 'POST';
                parameters.data = {
                    "name": vm.user.name,
                    "email": vm.user.email,
                    "message": vm.user.message,
                };
                parameters.callback = {
                    onSuccess: function(response) {
                        if (response.status == 201) {
                            var message = response.data.message;
                            $rootScope.notify("success", message);
                            // navigate to home page
                            $state.go('home');
                            vm.stopLoader();
                        }
                    },
                    onError: function(response) {
                        if (response.status == 400) {
                            vm.isFormError = true;
                            var isUsernameValid, isEmailValid, isMessageValid;
                            try {
                                isUsernameValid = response.data.name !== undefined ? true : false;
                                isEmailValid = response.data.email !== undefined ? true : false;
                                isMessageValid = response.data.message !== undefined ? true : false;
                                if (isUsernameValid) {
                                    vm.FormError = response.data.name[0];
                                } else if (isEmailValid) {
                                    vm.FormError = response.data.email[0];
                                } else if (isMessageValid) {
                                    vm.FormError = response.data.message[0];

                                } else {
                                    $rootScope.notify("error", "Some error occured. Please try again!");
                                }

                            } catch (error) {
                                $rootScope.notify("error", "Some error occured. Please try again!");
                            }
                        }

                        vm.stopLoader();
                    }
            };

                    utilities.sendRequest(parameters);
            }
        };
    }

})();

// Invoking IIFE for dashboard
(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('DashCtrl', DashCtrl);

    DashCtrl.$inject = ['utilities', '$state', '$rootScope'];

    function DashCtrl(utilities, $state, $rootScope) {
        var vm = this;

        vm.challengeCount = 0;
        vm.hostTeamCount = 0;
        vm.hostTeamExist = false;
        vm.participatedTeamCount = 0;
        // get token
        var userKey = utilities.getData('userKey');

        // store the next redirect value
        vm.redirectUrl = {};

        var parameters = {};
        parameters.url = 'auth/user/';
        parameters.method = 'GET';
        parameters.token = userKey;
        parameters.callback = {
            onSuccess: function(response) {
                var status = response.status;
                var details = response.data;
                if (status == 200) {
                    vm.name = details.username;
                }
            },
            onError: function(response) {
                var status = response.status;
                var error = response.data;
                if (status == 403) {
                    vm.error = error;

                    // navigate to permissions denied page
                    $state.go('web.permission-denied');
                } else if (status == 401) {
                    alert("Timeout, Please login again to continue!");
                    utilities.resetStorage();
                    $state.go("auth.login");
                    $rootScope.isAuth = false;

                }
            }
        };
        utilities.sendRequest(parameters);

        // get all ongoing challenges.
        parameters.url = 'challenges/challenge/present';
        parameters.method = 'GET';
        parameters.token = userKey;
        parameters.callback = {
            onSuccess: function(response) {
                var status = response.status;
                var details = response.data;
                if (status == 200) {
                    vm.challengeCount = details.results.length;
                    if (vm.hostTeamCount == 0) {
                        vm.hostTeamExist = false;
                    } else {
                        vm.hostTeamExist = true;
                    }
                }
            },
            onError: function(response) {
                var status = response.status;
                var error = response.data;
                if (status == 403) {
                    vm.error = error;

                    // navigate to permissions denied page
                    $state.go('web.permission-denied');
                } else if (status == 401) {
                    alert("Timeout, Please login again to continue!");
                    utilities.resetStorage();
                    $state.go("auth.login");
                    $rootScope.isAuth = false;

                }
            }
        };

        utilities.sendRequest(parameters);

        //check for host teams.
        parameters.url = 'hosts/challenge_host_team';
        parameters.method = 'GET';
        parameters.token = userKey;
        parameters.callback = {
            onSuccess: function(response) {
                var status = response.status;
                var details = response.data;
                if (status == 200) {
                    vm.hostTeamCount = details.count;
                }
            },
            onError: function(response) {
                var status = response.status;
                var error = response.data;
                if (status == 403) {
                    vm.error = error;

                    // navigate to permissions denied page
                    $state.go('web.permission-denied');
                } else if (status == 401) {
                    alert("Timeout, Please login again to continue!");
                    utilities.resetStorage();
                    $state.go("auth.login");
                    $rootScope.isAuth = false;

                }
            }
        };

        utilities.sendRequest(parameters);

        //check for participated teams.
        parameters.url = 'participants/participant_team';
        parameters.method = 'GET';
        parameters.token = userKey;
        parameters.callback = {
            onSuccess: function(response) {
                var status = response.status;
                var details = response.data;
                if (status == 200) {
                    vm.participatedTeamCount = details.count;
                }
            },
            onError: function(response) {
                var status = response.status;
                var error = response.data;
                if (status == 403) {
                    vm.error = error;

                    // navigate to permissions denied page
                    $state.go('web.permission-denied');
                } else if (status == 401) {
                    alert("Timeout, Please login again to continue!");
                    utilities.resetStorage();
                    $state.go("auth.login");
                    $rootScope.isAuth = false;

                }
            }
        };

        utilities.sendRequest(parameters);

        vm.hostChallenge = function() {
            $state.go('web.challenge-host-teams');
        };
    }

})();

// Invoking IIFE for challenge page
(function() {

    'use strict';
    angular
        .module('evalai')
        .controller('FeaturedChallengeCtrl', FeaturedChallengeCtrl);

    FeaturedChallengeCtrl.$inject = ['utilities', 'loaderService','$scope', '$state', '$http', '$stateParams'];

    function FeaturedChallengeCtrl(utilities, loaderService, $scope, $state, $http, $stateParams) {
        var vm = this;
        vm.challengeId = $stateParams.challengeId;
        vm.phaseSplitId = $stateParams.phaseSplitId;
        vm.phaseId = null;
        vm.wrnMsg = {};
        vm.page = {};
        vm.phases = {};
        vm.phaseSplits = {};
        vm.isValid = {};
        vm.isActive = false;
        vm.showUpdate = false;
        vm.showLeaderboardUpdate = false;
        vm.poller = null;
        vm.stopLeaderboard = function() {};

        // loader for existing teams
        vm.isExistLoader = false;
        vm.loaderTitle = '';
        vm.loaderContainer = angular.element('.exist-team-card');

        // show loader
        vm.startLoader = loaderService.startLoader;
        // stop loader
        vm.stopLoader = loaderService.stopLoader;
        vm.subErrors = {};

        utilities.showLoader();

        // get details of the particular challenge
        var parameters = {};
        parameters.url = 'challenges/challenge/' + vm.challengeId + '/';
        parameters.method = 'GET';
        parameters.data = {};
        parameters.callback = {
            onSuccess: function(response) {
                var details = response.data;
                vm.page = details;
                vm.isActive = details.is_active;


                if (vm.page.image === null) {
                    vm.page.image = "dist/images/logo.png";

                }
            },
            onError: function(response) {
                var error = response.data;
                utilities.storeData('emailError', error.detail);
                $state.go('web.permission-denied');
                utilities.hideLoader();
            }
        };

        utilities.sendRequest(parameters);

        // get details of the particular challenge phase
        parameters = {};
        parameters.url = 'challenges/challenge/' + vm.challengeId + '/challenge_phase';
        parameters.method = 'GET';
        parameters.data = {};
        parameters.callback = {
            onSuccess: function(response) {
                var details = response.data;
                vm.phases = details;
                // navigate to challenge page
                // $state.go('web.challenge-page.overview');
                utilities.hideLoader();
            },
            onError: function(response) {
                var error = response.data;
                utilities.storeData('emailError', error.detail);
                $state.go('web.permission-denied');
                utilities.hideLoader();
            }
        };

        utilities.sendRequest(parameters);

        // get details of the particular challenge phase split
        parameters = {};
        parameters.url = 'challenges/' + vm.challengeId + '/challenge_phase_split';
        parameters.method = 'GET';
        parameters.data = {};
        parameters.callback = {
            onSuccess: function(response) {
                var details = response.data;
                vm.phaseSplits = details;
                utilities.hideLoader();
            },
            onError: function(response) {
                var error = response.data;
                utilities.storeData('emailError', error.detail);
                $state.go('web.permission-denied');
                utilities.hideLoader();
            }
        };

        utilities.sendRequest(parameters);

        vm.getLeaderboard = function(phaseSplitId) {
            vm.isResult = true;
            vm.phaseSplitId = phaseSplitId;
            // loader for exisiting teams
            vm.isExistLoader = true;
            vm.loaderTitle = '';
            vm.loaderContainer = angular.element('.exist-team-card');


            vm.startLoader("Loading Leaderboard Items");

            // Show leaderboard
            vm.leaderboard = {};
            var parameters = {};
            parameters.url = "jobs/" + "challenge_phase_split/" + vm.phaseSplitId + "/leaderboard/?page_size=1000";
            parameters.method = 'GET';
            parameters.data = {};
            parameters.callback = {
                onSuccess: function(response) {
                    var details = response.data;
                    vm.leaderboard = details.results;
                    vm.phase_name = vm.phaseSplitId;
                    vm.stopLoader();
                },
                onError: function(response) {
                    var error = response.data;
                    vm.leaderboard.error = error;
                    vm.stopLoader();
                }
            };

            utilities.sendRequest(parameters);
        };

        if (vm.phaseSplitId) {
            vm.getLeaderboard(vm.phaseSplitId);
        }
    }

})();

// Invoking IIFE
(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('MainCtrl', MainCtrl);

    MainCtrl.$inject = ['utilities', '$rootScope', '$state'];

    function MainCtrl(utilities, $rootScope, $state) {

        var vm = this;
        vm.user = {};
        vm.challengeList = [];
        vm.isChallenge = true;
        vm.isMore = false;
        // store the next redirect value
        vm.redirectUrl = {};


        vm.getChallenge = function() {
            // get featured challenge (unauthorized)
            var parameters = {};
            parameters.url = 'challenges/challenge/present';
            parameters.method = 'GET';
            parameters.token = null;
            parameters.callback = {
                onSuccess: function(response) {
                    vm.challengeList = response.data;
                    var challengeCount = vm.challengeList.count;
                    if (challengeCount === 0) {
                        vm.isChallenge = false;
                    } else {
                        vm.isChallenge = true;
                        vm.featuredChallenge = vm.challengeList.results[0];
                        if (vm.featuredChallenge.description.length > 120) {
                            vm.isMore = true;
                        } else {
                            vm.isMore = false;
                        }
                    }
                },
                onError: function() {}
            };
            utilities.sendRequest(parameters);
        };


        vm.init = function() {
            // Check if token is available in localstorage
            var userKey = utilities.getData('userKey');
            // check for authenticated user
            if (userKey) {
                var parameters = {};
                parameters.url = 'auth/user/';
                parameters.method = 'GET';
                parameters.token = userKey;
                parameters.callback = {
                    onSuccess: function(response) {
                        var status = response.status;
                        var details = response.data;
                        if (status == 200) {
                            vm.user.name = details.username;
                        }
                    },
                    onError: function(response) {
                        var status = response.status;
                        if (status == 401) {
                            utilities.resetStorage();
                            $state.go("auth.login");
                            $rootScope.isAuth = false;
                        }
                    }
                };
                utilities.sendRequest(parameters);
            }
        };


        vm.hostChallenge = function() {
            if ($rootScope.isAuth === true) {
                $state.go('web.challenge-host-teams');
            } else {
                $state.go('auth.login');
                $rootScope.previousState = "web.challenge-host-teams";
            }
        };


        vm.profileDropdown = function() {
            angular.element(".dropdown-button").dropdown();
        };


        vm.init();
        vm.getChallenge();

    }
})();

// Invoking IIFE for our team

(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('ourTeamCtrl', ourTeamCtrl);

    ourTeamCtrl.$inject = ['utilities'];

    function ourTeamCtrl(utilities) {
        /* jshint validthis: true */
        var vm = this;

        var parameters = {};
        parameters.url = 'web/team/';
        parameters.method = 'GET';
        parameters.callback = {
            onSuccess: function(response) {
                var status = response.status;
                var results = response.data;
                if (status == 200) {
                    if (results.length !== 0) {
                        var coreTeamList = [];
                        var contributingTeamList = [];
                        for (var i = 0; i < results.length; i++) {
                            if (results[i].team_type === "Core Team") {
                                vm.coreTeamType = results[i].team_type;
                                vm.coreTeamList = coreTeamList.push(results[i]);

                            } else if (results[i].team_type === "Contributor") {
                                vm.contributingTeamType = results[i].team_type;
                                vm.contributingTeamList = contributingTeamList.push(results[i]);
                            }
                            vm.coreTeamDetails = coreTeamList;
                            vm.contributingTeamDetails = contributingTeamList;
                        }
                    } else {
                        vm.noTeamDisplay = "Team will be updated very soon !";
                    }
                }
            },
            onError: function() {}
        };

        utilities.sendRequest(parameters, "no-header");
    }
})();

// Invoking IIFE for permission denied
(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('PermCtrl', PermCtrl);

    PermCtrl.$inject = ['utilities'];

    function PermCtrl(utilities) {
        var vm = this;

        // message for not verified users
        vm.emailError = utilities.getData('emailError');
        //user email redirect
        vm.user={};

        var userKey = utilities.getData('userKey');

        var parameters = {};
        parameters.url = 'auth/user/';
        parameters.method = 'GET';
        parameters.token = userKey;
        parameters.callback = {
            onSuccess: function(response) {
                var status = response.status;
                var result = response.data;
                vm.user = result;
            },
        };

        utilities.sendRequest(parameters);

    }

})();

// Invoking IIFE for profile view

(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('profileCtrl', profileCtrl);

    profileCtrl.$inject = ['utilities', '$rootScope'];

    function profileCtrl(utilities, $rootScope) {
        var vm = this;

        vm.user = {};
        vm.countLeft = 0;
        vm.compPerc = 0;
        var count = 0;

        utilities.hideLoader();

        vm.imgUrlObj = {
            profilePic: "dist/images/spaceman.png"
        };

        var hasImage = utilities.getData('avatar');
        if (!hasImage) {
            vm.imgUrl = _.sample(vm.imgUrlObj);
            utilities.storeData('avatar', vm.imgUrl);
        } else {
            vm.imgUrl = utilities.getData('avatar');
        }

        // get token
        var userKey = utilities.getData('userKey');

        var parameters = {};
        parameters.url = 'auth/user/';
        parameters.method = 'GET';
        parameters.token = userKey;
        parameters.callback = {
            onSuccess: function(response) {
                var status = response.status;
                var result = response.data;
                if (status == 200) {
                    for (var i in result) {
                        if (result[i] === "" || result[i] === undefined || result[i] === null) {
                            result[i] = "-";
                            vm.countLeft = vm.countLeft + 1;
                        }
                        count = count + 1;
                    }
                    vm.compPerc = parseInt((vm.countLeft / count) * 100);

                    vm.user = result;
                    vm.user.complete = 100 - vm.compPerc;

                }
            },
            onError: function() {
                $rootScope.notify("error", "Some error have occured , please try again !");
            }
        };

        utilities.sendRequest(parameters);
    }

})();

// Invoking IIFE for teams
(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('TeamsCtrl', TeamsCtrl);

    TeamsCtrl.$inject = ['utilities','loaderService', '$scope', '$state', '$http', '$rootScope', '$mdDialog'];

    function TeamsCtrl(utilities,loaderService, $scope, $state, $http, $rootScope, $mdDialog) {
        var vm = this;
        // console.log(vm.teamId)
        var userKey = utilities.getData('userKey');
        var challengePk = 1;

        utilities.showLoader();

        // default variables/objects
        vm.team = {};
        vm.teamId = null;
        vm.existTeam = {};
        vm.currentPage = '';
        vm.isNext = '';
        vm.isPrev = '';
        vm.team.error = false;
        vm.showPagination = false;

        // loader for existng teams// loader for exisiting teams
        vm.isExistLoader = false;
        vm.loaderTitle = '';
        vm.loaderContainer = angular.element('.exist-team-card');

        // show loader
        vm.startLoader = loaderService.startLoader;
        vm.stopLoader = loaderService.stopLoader;

        vm.activateCollapsible = function() {
            angular.element('.collapsible').collapsible();
        };

        var parameters = {};
        parameters.url = 'participants/participant_team';
        parameters.method = 'GET';
        parameters.token = userKey;
        parameters.callback = {
            onSuccess: function(response) {
                var status = response.status;
                var details = response.data;
                if (status == 200) {
                    vm.existTeam = details;

                    if (vm.existTeam.count === 0) {
                        vm.showPagination = false;
                        vm.paginationMsg = "No team exists for now, start by creating a new team!";
                    } else {
                        vm.activateCollapsible();
                        vm.showPagination = true;
                        vm.paginationMsg = "";
                    }
                    // clear error msg from storage
                    utilities.deleteData('emailError');

                    // condition for pagination
                    if (vm.existTeam.next === null) {
                        vm.isNext = 'disabled';
                    } else {
                        vm.isNext = '';
                    }

                    if (vm.existTeam.previous === null) {
                        vm.isPrev = 'disabled';
                    } else {
                        vm.isPrev = '';
                    }
                    if (vm.existTeam.next !== null) {
                        vm.currentPage = vm.existTeam.next.split('page=')[1] - 1;
                    } else {
                        vm.currentPage = 1;
                    }


                    // select team from existing list
                    vm.selectExistTeam = function() {

                        // loader for exisiting teams
                        vm.isExistLoader = true;
                        vm.loaderTitle = '';
                        vm.loaderContainer = angular.element('.exist-team-card');


                        vm.startLoader("Loading Teams");
                        // loader end

                        var parameters = {};
                        parameters.url = 'challenges/challenge/' + challengePk + '/participant_team/' + vm.teamId;
                        parameters.method = 'POST';
                        parameters.token = userKey;
                        parameters.callback = {
                            onSuccess: function() {
                                $state.go('web.challenge-page.overview');
                                vm.stopLoader();
                            },
                            onError: function() {
                                vm.existTeamError = "Please select a team";
                                vm.stopLoader();
                            }
                        };
                        utilities.sendRequest(parameters);
                    };

                    // to load data with pagination
                    vm.load = function(url) {
                        // loader for exisiting teams
                        vm.isExistLoader = true;
                        vm.loaderTitle = '';
                        vm.loaderContainer = angular.element('.exist-team-card');


                        vm.startLoader("Loading Teams");
                        if (url !== null) {

                            //store the header data in a variable
                            var headers = {
                                'Authorization': "Token " + userKey
                            };

                            //Add headers with in your request
                            $http.get(url, { headers: headers }).then(function(response) {
                                // reinitialized data
                                var details = response.data;
                                vm.existTeam = details;

                                // condition for pagination
                                if (vm.existTeam.next === null) {
                                    vm.isNext = 'disabled';
                                    vm.currentPage = vm.existTeam.count / 10;
                                } else {
                                    vm.isNext = '';
                                    vm.currentPage = parseInt(vm.existTeam.next.split('page=')[1] - 1);
                                }

                                if (vm.existTeam.previous === null) {
                                    vm.isPrev = 'disabled';
                                } else {
                                    vm.isPrev = '';
                                }
                                vm.stopLoader();
                            });
                        } else {
                            vm.stopLoader();
                        }
                    };

                }
                utilities.hideLoader();
            },
            onError: function(response) {
                var error = response.data;
                utilities.storeData('emailError', error.detail);
                $state.go('web.permission-denied');
                utilities.hideLoader();
            }
        };

        utilities.sendRequest(parameters);

        // function to create new team
        vm.createNewTeam = function() {
            vm.isExistLoader = true;
            vm.loaderTitle = '';
            vm.loaderContainer = angular.element('.new-team-card');

            // show loader

            vm.startLoader("Loading Teams");

            var parameters = {};
            parameters.url = 'participants/participant_team';
            parameters.method = 'POST';
            parameters.data = {
                "team_name": vm.team.name
            };
            parameters.token = userKey;
            parameters.callback = {
                onSuccess: function() {
                    $rootScope.notify("success", "Team " + vm.team.name + " has been created successfully!");
                    vm.team.error = false;
                    vm.stopLoader();
                    vm.team.name = '';

                    vm.startLoader("Loading Teams");
                    var parameters = {};
                    parameters.url = 'participants/participant_team';
                    parameters.method = 'GET';
                    parameters.token = userKey;
                    parameters.callback = {
                        onSuccess: function(response) {
                            var status = response.status;
                            var details = response.data;
                            if (status == 200) {
                                vm.existTeam = details;
                                vm.showPagination = true;
                                vm.paginationMsg = '';


                                // condition for pagination
                                if (vm.existTeam.next === null) {
                                    vm.isNext = 'disabled';
                                    vm.currentPage = 1;
                                } else {
                                    vm.isNext = '';
                                    vm.currentPage = vm.existTeam.next.split('page=')[1] - 1;
                                }

                                if (vm.existTeam.previous === null) {
                                    vm.isPrev = 'disabled';
                                } else {
                                    vm.isPrev = '';
                                }


                                vm.stopLoader();
                            }
                        },
                        onError: function() {
                            vm.stopLoader();
                        }
                    };
                    utilities.sendRequest(parameters);
                },
                onError: function(response) {
                    var error = response.data;

                    vm.team.error = error.team_name[0];
                    vm.stopLoader();
                    $rootScope.notify("error", "New team couldn't be created.");
                }
            };

            utilities.sendRequest(parameters);

        };

        vm.confirmDelete = function(ev, participantTeamId) {
            ev.stopPropagation();
            // Appending dialog to document.body to cover sidenav in docs app
            var confirm = $mdDialog.confirm()
                .title('Would you like to remove yourself?')
                .textContent('Note: This action will remove you from the team.')
                .ariaLabel('Lucky day')
                .targetEvent(ev)
                .ok('Yes')
                .cancel("No");

            $mdDialog.show(confirm).then(function() {
                vm.startLoader();
                var parameters = {};
                parameters.url = 'participants/remove_self_from_participant_team/' + participantTeamId;
                parameters.method = 'DELETE';
                parameters.data = {};
                parameters.token = userKey;
                parameters.callback = {
                    onSuccess: function() {

                        vm.team.error = false;
                        $rootScope.notify("info", "You have removed yourself successfully");

                        var parameters = {};
                        parameters.url = 'participants/participant_team';
                        parameters.method = 'GET';
                        parameters.token = userKey;
                        parameters.callback = {
                            onSuccess: function(response) {
                                var status = response.status;
                                var details = response.data;
                                if (status == 200) {
                                    vm.existTeam = details;


                                    // condition for pagination
                                    if (vm.existTeam.next === null) {
                                        vm.isNext = 'disabled';
                                        vm.currentPage = vm.existTeam.count / 10;
                                    } else {
                                        vm.isNext = '';
                                        vm.currentPage = parseInt(vm.existTeam.next.split('page=')[1] - 1);
                                    }

                                    if (vm.existTeam.previous === null) {
                                        vm.isPrev = 'disabled';
                                    } else {
                                        vm.isPrev = '';
                                    }


                                    if (vm.existTeam.count === 0) {

                                        vm.showPagination = false;
                                        vm.paginationMsg = "No team exists for now, start by creating a new team!";
                                    } else {
                                        vm.showPagination = true;
                                        vm.paginationMsg = "";
                                    }
                                }

                                vm.stopLoader();
                            }
                        };
                        utilities.sendRequest(parameters);
                    },
                    onError: function(response) {
                        var error = response.data['error'];
                        vm.stopLoader();
                        $rootScope.notify("error", error);
                    }
                };

                utilities.sendRequest(parameters);

            }, function() {
            });
        };


        vm.inviteOthers = function(ev, participantTeamId) {
            ev.stopPropagation();
            // Appending dialog to document.body to cover sidenav in docs app
            var confirm = $mdDialog.prompt()
                .title('Invite others to this team')
                .textContent('Enter the email address of the person')
                .placeholder('email')
                .ariaLabel('')
                .targetEvent(ev)
                .ok('Send Invite')
                .cancel('Cancel');

            $mdDialog.show(confirm).then(function(result) {
                var parameters = {};
                parameters.url = 'participants/participant_team/' + participantTeamId + '/invite';
                parameters.method = 'POST';
                parameters.data = {
                    "email": result
                };
                parameters.token = userKey;
                parameters.callback = {
                    onSuccess: function(response) {
                        var message = response.data['message'];
                        $rootScope.notify("success", message);
                    },
                    onError: function(response) {
                        var error = response.data['error'];
                        $rootScope.notify("error", error);
                    }
                };

                utilities.sendRequest(parameters);
            }, function() {
            });
        };
    }

})();

// Invoking IIFE for update profile

(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('updateProfileCtrl', updateProfileCtrl);

    updateProfileCtrl.$inject = ['utilities', '$state', '$http', '$rootScope'];

    function updateProfileCtrl(utilities, $state, $http, $rootScope) {
        var vm = this;
        var userKey = utilities.getData('userKey');
        vm.wrnMsg = {};
        vm.isValid = {};
        vm.user = {};
        vm.isFormError = false;

        vm.updateprofileContainer = angular.element('.update-profile-card');

        vm.startLoader = function(msg) {
            $rootScope.isLoader = true;
            $rootScope.loaderTitle = msg;
            vm.updateprofileContainer.addClass('low-screen');
        };

        // stop loader
        vm.stopLoader = function() {
            $rootScope.isLoader = false;
            $rootScope.loaderTitle = '';
            vm.updateprofileContainer.removeClass('low-screen');
        };

        // To get the previous profile data
        var parameters = {};
        parameters.url = 'auth/user/';
        parameters.method = 'GET';
        parameters.token = userKey;
        parameters.callback = {
            onSuccess: function(response) {
                var status = response.status;
                var result = response.data;
                if (status == 200) {
                    vm.user = result;
                }

            },
            onError: function() {
                $rootScope.notify("error", "Error in loading profile, please try again later !");
            }
        };

        utilities.sendRequest(parameters);

        // function to update Profile
        vm.updateProfile = function(resetconfirmFormValid) {
            if (resetconfirmFormValid) {

                vm.startLoader("Updating Your Profile");
                var parameters = {};
                parameters.url = 'auth/user/';
                parameters.method = 'PUT';
                parameters.data = {
                    "username": vm.user.username,
                    "first_name": vm.user.first_name,
                    "last_name": vm.user.last_name,
                };
                parameters.token = userKey;
                parameters.callback = {
                    onSuccess: function(response) {
                        if (response.status == 200) {
                            $rootScope.notify("success", "Profile updated successfully!");
                            // navigate to profile page
                            $state.go('web.profile');
                            vm.stopLoader();
                        }
                    },
                    onError: function(response) {
                        if (response.status == 400) {
                            vm.stopLoader();
                            vm.isFormError = true;
                            var isUsername_valid, isFirstname_valid, isLastname_valid;
                            try {
                                isUsername_valid = typeof(response.data.username) !== 'undefined' ? true : false;
                                isFirstname_valid = typeof(response.data.first_name) !== 'undefined' ? true : false;
                                isLastname_valid = typeof(response.data.last_name) !== 'undefined' ? true : false;
                                if (isUsername_valid) {
                                    vm.FormError = response.data.username[0];
                                } else if (isFirstname_valid) {
                                    vm.FormError = response.data.first_name[0];
                                } else if (isLastname_valid) {
                                    vm.FormError = response.data.last_name[0];

                                } else {
                                    $rootScope.notify("error", "Some error have occured . Please try again !");
                                }

                            } catch (error) {
                                $rootScope.notify("error", "Some error have occured . Please try again !");
                            }
                        }

                        vm.stopLoader();
                    }
                };

                utilities.sendRequest(parameters);

            } else {
                $rootScope.notify("error", "Form fields are not valid!");
                vm.stopLoader();
            }
        };
    }

})();

// Invoking IIFE for dashboard

(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('WebCtrl', WebCtrl);

    WebCtrl.$inject = ['utilities', '$state', '$stateParams', '$rootScope'];

    function WebCtrl(utilities, $state, $stateParams, $rootScope) {
        var vm = this;

        vm.user = {};

        utilities.hideLoader();

        angular.element().find(".side-intro").addClass("z-depth-3");

        // get token
        var userKey = utilities.getData('userKey');

        var parameters = {};
        parameters.url = 'auth/user/';
        parameters.method = 'GET';
        parameters.token = userKey;
        parameters.callback = {
            onSuccess: function(response) {
                var status = response.status;
                var result = response.data;
                if (status == 200) {
                    vm.name = result.username;
                }
            },
            onError: function() {
                $rootScope.notify("error", "Some error have occured , please try again !");
            }
        };

        utilities.sendRequest(parameters);
    }

})();
