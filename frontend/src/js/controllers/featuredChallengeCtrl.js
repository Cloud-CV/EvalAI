// Invoking IIFE for challenge page
(function() {

    'use strict';
    angular
        .module('evalai')
        .controller('FeaturedChallengeCtrl', FeaturedChallengeCtrl);

    FeaturedChallengeCtrl.$inject = ['utilities', '$scope', '$state', '$http', '$stateParams'];

    function FeaturedChallengeCtrl(utilities, $scope, $state, $http, $stateParams) {
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
        vm.loginContainer = angular.element('.exist-team-card');

        // show loader
        vm.startExistLoader = function(msg) {
            vm.isExistLoader = true;
            vm.loaderTitle = msg;
            vm.loginContainer.addClass('low-screen');
        };

        // stop loader
        vm.stopExistLoader = function() {
            vm.isExistLoader = false;
            vm.loaderTitle = '';
            vm.loginContainer.removeClass('low-screen');
        };

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
            vm.loginContainer = angular.element('.exist-team-card');

            // show loader
            vm.startLoader = function(msg) {
                vm.isExistLoader = true;
                vm.loaderTitle = msg;
                vm.loginContainer.addClass('low-screen');
            };

            // stop loader
            vm.stopLoader = function() {
                vm.isExistLoader = false;
                vm.loaderTitle = '';
                vm.loginContainer.removeClass('low-screen');
            };

            vm.startLoader("Loading Leaderboard Items");

            // Show leaderboard
            vm.leaderboard = {};
            var parameters = {};
            parameters.url = "jobs/" + "challenge_phase_split/" + vm.phaseSplitId + "/leaderboard/";
            parameters.method = 'GET';
            parameters.data = {};
                parameters.callback = {
                onSuccess: function(response) {
                    var details = response.data;
                    vm.leaderboard = details.results;
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
    }

})();
