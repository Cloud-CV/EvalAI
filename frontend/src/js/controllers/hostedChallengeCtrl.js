(function () {

    'use strict';

    angular
        .module('evalai')
        .controller('HostedChallengesCtrl', HostedChallengesCtrl);

    HostedChallengesCtrl.$inject = ['utilities', '$rootScope', '$mdDialog', '$filter'];

    function HostedChallengesCtrl(utilities, $rootScope, $mdDialog, $filter) {
        var vm = this;
        var userKey = utilities.getData('userKey');

        utilities.showLoader();
        var gmtOffset = moment().utcOffset();
        var gmtSign = gmtOffset >= 0 ? '+' : '-';
        var gmtHours = Math.abs(Math.floor(gmtOffset / 60));
        var gmtMinutes = Math.abs(gmtOffset % 60);
        var gmtZone = 'GMT ' + gmtSign + ' ' + gmtHours + ':' + (gmtMinutes < 10 ? '0' : '') + gmtMinutes;

        vm.challengeList = [];
        vm.ongoingChallenges = [];
        vm.upcomingChallenges = [];
        vm.pastChallenges = [];
        vm.challengeCreator = {};
        vm.searchTitle = [];
        vm.selecteddomain = [];
        vm.selectedHostTeam = '';
        vm.sortByTeam = '';
        vm.host_team_choices = [];
        vm.filterStartDate = null;
        vm.filterEndDate = null;
        vm.currentTab = 'ongoing';


        vm.setCurrentTab = function (tabName) {
            vm.currentTab = tabName;
        };

        vm.getCurrentChallengeList = function () {
            if (vm.currentTab === 'ongoing') {
                return vm.ongoingChallenges;
            } else if (vm.currentTab === 'upcoming') {
                return vm.upcomingChallenges;
            } else if (vm.currentTab === 'past') {
                return vm.pastChallenges;
            } else {
                return [];
            }
        };
        
        var parameters = {};
        parameters.url = 'hosts/challenge_host_team/';
        parameters.method = 'GET';
        parameters.token = userKey;
        parameters.callback = {
            onSuccess: function (response) {
                var host_teams = response["data"]["results"];
                parameters.method = 'GET';
                var timezone = moment.tz.guess();
                for (var i = 0; i < host_teams.length; i++) {
                    parameters.url = "challenges/challenge_host_team/" + host_teams[i]["id"] + "/challenge";
                    parameters.callback = {
                        onSuccess: function (response) {
                            var data = response.data;
                            var current = new Date();
                            for (var j = 0; j < data.results.length; j++) {
                                var challenge = data.results[j];
                                vm.challengeList.push(challenge);
                                var id = challenge.id;
                                vm.challengeCreator[id] = challenge.creator.id;
                                utilities.storeData("challengeCreator", vm.challengeCreator);
                                var offset = new Date(challenge.start_date).getTimezoneOffset();
                                challenge.time_zone = moment.tz.zone(timezone).abbr(offset);
                                challenge.gmt_zone = gmtZone;

                                var startDate = new Date(challenge.start_date);
                                var endDate = new Date(challenge.end_date);

                                if (startDate > current) {
                                    if (!vm.upcomingChallenges.some(c => c.id === challenge.id)) {
                                        vm.upcomingChallenges.push(challenge);
                                    }
                                }
                                else if (current >= startDate && current <= endDate) {
                                    if (!vm.ongoingChallenges.some(c => c.id === challenge.id)) {
                                        vm.ongoingChallenges.push(challenge);
                                    }
                                }
                                else if (current > endDate) {
                                    if (!vm.pastChallenges.some(c => c.id === challenge.id)) {
                                        vm.pastChallenges.push(challenge);
                                    }
                                }
                            }
                        },
                        onError: function () {
                            utilities.hideLoader();
                        }
                    };
                    utilities.sendRequest(parameters);
                }
                utilities.hideLoader();
            },
            onError: function () {
                utilities.hideLoader();
            }
        };
        utilities.sendRequest(parameters);

        vm.getFilteredOngoingChallenges = function () {
            let result = $filter('customTitleFilter')(vm.ongoingChallenges, vm.searchTitle);
            result = $filter('customDomainFilter')(result, vm.selecteddomain);
            result = $filter('customHostFilter')(result, vm.selectedHostTeam);
            result = $filter('customDateRangeFilter')(result, vm.filterStartDate, vm.filterEndDate);
            result = $filter('orderBy')(result, 'creator.team_name', vm.sortByTeam === 'desc');
            return result;
        };
        vm.getFilteredUpcomingChallenges = function () {
            let result = $filter('customTitleFilter')(vm.upcomingChallenges, vm.searchTitle);
            result = $filter('customDomainFilter')(result, vm.selecteddomain);
            result = $filter('customHostFilter')(result, vm.selectedHostTeam);
            result = $filter('customDateRangeFilter')(result, vm.filterStartDate, vm.filterEndDate);
            result = $filter('orderBy')(result, 'creator.team_name', vm.sortByTeam === 'desc');
            return result;
        };
        vm.getFilteredPastChallenges = function () {
            let result = $filter('customTitleFilter')(vm.pastChallenges, vm.searchTitle);
            result = $filter('customDomainFilter')(result, vm.selecteddomain);
            result = $filter('customHostFilter')(result, vm.selectedHostTeam);
            result = $filter('customDateRangeFilter')(result, vm.filterStartDate, vm.filterEndDate);
            result = $filter('orderBy')(result, 'creator.team_name', vm.sortByTeam === 'desc');
            return result;
        };

        function extractUniqueHostTeams() {
            const allChallenges = [].concat(
                vm.currentList || [],
                vm.upcomingList || [],
                vm.pastList || []
            );

            const hostTeamsSet = new Set();

            allChallenges.forEach(function (challenge) {
                if (challenge.creator && challenge.creator.team_name) {
                    hostTeamsSet.add(challenge.creator.team_name);
                }
            });

            vm.host_team_choices = Array.from(hostTeamsSet).sort();
        }

        // Delay extraction slightly to ensure data is populated
        setTimeout(function () {
            extractUniqueHostTeams();
        }, 1000);

        parameters.url = "challenges/challenge/get_domain_choices/";
        parameters.method = 'GET';
        parameters.data = {};
        vm.domain_choices = [];
        parameters.callback = {
            onSuccess: function (response) {
                vm.domain_choices.push(["All", "All"]);
                for (var i = 0; i < response.data.length; i++) {
                    vm.domain_choices.push([response.data[i][0], response.data[i][1]]);
                }
                vm.domain_choices.push(["None", "None"]);
            },
            onError: function (response) {
                var error = response.data;
                $rootScope.notify("error", error);
            }
        };
        utilities.sendRequest(parameters);

        vm.resetFilter = function () {
            vm.selecteddomain = [];
            vm.searchTitle = [];
            vm.selectedHostTeam = '';
            vm.sortByTeam = '';
            vm.filterStartDate = null;
            vm.filterEndDate = null;
        };

        

        vm.openFilterDialog = function (ev) {
            console.log("Filter dialog opened");
            $mdDialog.show({
                controller: FilterDialogController,
                controllerAs: 'dialog',
                templateUrl: 'src/views/web/challenge/challenge-filter-dialog.html',
                parent: angular.element(document.body),
                targetEvent: ev,
                clickOutsideToClose: true,
                fullscreen: true,
                locals: {
                    filterData: {
                        selecteddomain: vm.selecteddomain,
                        selectedHostTeam: vm.selectedHostTeam,
                        sortByTeam: vm.sortByTeam,
                        filterStartDate: vm.filterStartDate,
                        filterEndDate: vm.filterEndDate,
                        domain_choices: vm.domain_choices,
                        host_team_choices: vm.host_team_choices
                    }
                }
            }).then(function (filters) {
                vm.selecteddomain = filters.selecteddomain;
                vm.selectedHostTeam = filters.selectedHostTeam;
                vm.sortByTeam = filters.sortByTeam;
                vm.filterStartDate = filters.filterStartDate;
                vm.filterEndDate = filters.filterEndDate;
            });
        };

        

        

    }

    angular.module('evalai')
        .controller('FilterDialogController', FilterDialogController);

    FilterDialogController.$inject = ['$scope', '$mdDialog', 'filterData'];

    function FilterDialogController($scope, $mdDialog, filterData) {
        $scope.selecteddomain = filterData.selecteddomain;
        $scope.selectedHostTeam = filterData.selectedHostTeam;
        $scope.sortByTeam = filterData.sortByTeam;
        $scope.filterStartDate = filterData.filterStartDate;
        $scope.filterEndDate = filterData.filterEndDate;
        $scope.domain_choices = filterData.domain_choices;
        $scope.host_team_choices = filterData.host_team_choices;

        $scope.apply = function () {
            $mdDialog.hide({
                selecteddomain: $scope.selecteddomain,
                selectedHostTeam: $scope.selectedHostTeam,
                sortByTeam: $scope.sortByTeam,
                filterStartDate: $scope.filterStartDate,
                filterEndDate: $scope.filterEndDate
            });
        };

        $scope.cancel = function () {
            $mdDialog.cancel();
        };
    }
})();
