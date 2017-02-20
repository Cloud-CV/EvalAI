// TODO Still need to work on this file. NOT COMPLETED YET
(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('ChallengeCreateCtrl', ChallengeCreateCtrl);

    ChallengeCreateCtrl.$inject = ['utilities', '$state', '$http', '$rootScope'];

    function ChallengeCreateCtrl(utilities, $state, $http, $rootScope) {
        var vm = this;
        var userKey = utilities.getData('userKey');
        var hostTeamId = utilities.getData('challengeHostTeamPk');
        vm.wrnMsg = {};
        vm.isValid = {};

        // function to create a challenge
        vm.createChallenge = function() {
            var parameters = {};
            parameters.url = 'challenges/challenge_host_team/' + hostTeamId +'/challenge';
            parameters.method = 'POST';
            parameters.data = {
                "title": vm.title,
                "description": vm.description,
                "terms_and_conditions": vm.terms_and_conditions,
                "submission_guidelines": vm.submission_guidelines,
                "published": vm.published,
                "anonymous_leaderboard": vm.anonymous_leaderboard,
                "start_date": vm.start_date,
                "end_date": vm.end_date
            };

            parameters.token = userKey;
            parameters.callback = {
                onSuccess: function(response) {
                    var status = response.status;
                    /* jshint shadow:true */
                    var response = response.data;
                    console.log(response);
                    // navigate to Challenge List Page
                    $state.go('web.challenge-main.challenge-list');
                },
                onError: function(response) {
                    var status = response.status;
                    var error = response.data;
                    console.log("Error");
                    console.log(error);
                    angular.forEach(error, function(value, key) {
                        if (key == 'title') {
                            vm.isValid.title = true;
                            vm.wrnMsg.title = value[0];
                        }
                        if (key == 'description') {
                            vm.isValid.description = true;
                            vm.wrnMsg.description = value[0];
                        }
                        if (key == 'terms_and_conditions') {
                            vm.isValid.terms_and_conditions = true;
                            vm.wrnMsg.terms_and_conditions = value[0];
                        }
                        if (key == 'submission_guidelines') {
                            vm.isValid.submission_guidelines = true;
                            vm.wrnMsg.submission_guidelines = value[0];
                        }
                        if (key == 'published') {
                            vm.isValid.published = true;
                            vm.wrnMsg.published = value[0];
                        }
                        if (key == 'anonymous_leaderboard') {
                            vm.isValid.anonymous_leaderboard = true;
                            vm.wrnMsg.anonymous_leaderboard = value[0];
                        }
                        if (key == 'start_date') {
                            vm.isValid.start_date = true;
                            vm.wrnMsg.start_date = value[0];
                        }
                        if (key == 'end_date') {
                            vm.isValid.end_date = true;
                            vm.wrnMsg.end_date = value[0];
                        }
                    });
                }
            };

            utilities.sendRequest(parameters);
        };
    }

})();
