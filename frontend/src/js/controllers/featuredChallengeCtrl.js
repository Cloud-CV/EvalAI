// Invoking IIFE for challenge page
(function() {

    'use strict';
    angular
        .module('evalai')
        .controller('FeaturedChallengeCtrl', FeaturedChallengeCtrl);

    FeaturedChallengeCtrl.$inject = ['utilities', 'loaderService','$scope', '$state', '$http', '$stateParams', 'moment'];

    function FeaturedChallengeCtrl(utilities, loaderService, $scope, $state, $http, $stateParams, moment) {
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
                    for (var i=0; i<vm.leaderboard.length; i++) {
                        var dateTimeNow = moment(new Date());
                        var submissionTime = moment(vm.leaderboard[i].submission__submitted_at);
                        var duration = moment.duration(dateTimeNow.diff(submissionTime));
                        if (duration._data.hours > 24) {
                            var hours = duration.asHours();
                            vm.leaderboard[i].submission__submitted_at = hours;
                            if (hours.toFixed(0)==1) {
                                vm.timeSpan = 'hour';
                            } else {
                                vm.timeSpan = 'hours';
                            }                        } 
                        else if (duration._data.days > 0) {
                            var days = duration.asDays();
                            vm.leaderboard[i].submission__submitted_at = days;
                            if (days.toFixed(0)==1) {
                                vm.timeSpan = 'day';
                            } else {
                                vm.timeSpan = 'days';
                            }
                        }
                        else if (duration._data.days > 30 || duration._data.days > 31) {
                            var months = duration.asMonths();
                            vm.leaderboard[i].submission__submitted_at = months;
                            if (months.toFixed(0)==1) {
                                vm.timeSpan = 'month';
                            } else {
                                vm.timeSpan = 'months';
                            }
                        }
                        else if (duration._data.months > 12) {
                            var years = duration.asYears();
                            vm.leaderboard[i].submission__submitted_at = years;
                            if (years.toFixed(0)==1) {
                                vm.timeSpan = 'year';
                            } else {
                                vm.timeSpan = 'years';
                            }
                        }
                    }
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
