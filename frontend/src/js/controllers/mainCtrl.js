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
        vm.gridActiveOrganizations = []


        vm.getChallenge = function() {
            // get featured challenge (unauthorized)
            var parameters = {};
            parameters.url = 'challenges/featured/';
            parameters.method = 'GET';
            parameters.token = null;
            parameters.callback = {
                onSuccess: function(response) {
                    vm.challengeList = response.data;
                },
                onError: function() {}
            };
            utilities.sendRequest(parameters);
        };

        vm.listToMatrix = function(list, colSize) {
            var grid = [], i = 0, x = list.length, col, row = -1;
            for (var i = 0; i < x; i++) {
                col = i % colSize;
                if (col === 0) {
                    grid[++row] = [];
                }
                var logoId = list[i]["name"].replace(/\s+/g, '-').toLowerCase() + "-logo";
                list[i]["logoId"] = logoId;
                grid[row][col] = list[i];
            }
            return grid;
        }

        vm.getActiveOrganizations = function() {
            // get featured challenge (unauthorized)
            var parameters = {};
            parameters.url = 'web/get_active_organizations/';
            parameters.method = 'GET';
            parameters.token = null;
            parameters.callback = {
                onSuccess: function(response) {
                    var activeOrganizationsList = response.data;
                    vm.gridActiveOrganizations = vm.listToMatrix(activeOrganizationsList, 6);
                },
                onError: function(response) {
                    var status = response.status;
                }
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
        vm.getActiveOrganizations();
        angular.element('.carousel').carousel({
            duration: 200
            // dist: 0,
            // indicators: true
        });
    }
})();
