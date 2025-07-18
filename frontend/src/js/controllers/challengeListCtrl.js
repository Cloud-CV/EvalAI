// Invoking IIFE for challenge page
(function () {

    'use strict';
    angular
        .module('evalai')
        .controller('ChallengeListCtrl', ChallengeListCtrl);

    ChallengeListCtrl.$inject = ['utilities', '$window', 'moment', '$rootScope', '$mdDialog', '$filter'];

    function ChallengeListCtrl(utilities, $window, moment, $rootScope, $mdDialog,$filter) {
        var vm = this;
        var userKey = utilities.getData('userKey');
        var gmtOffset = moment().utcOffset();
        var gmtSign = gmtOffset >= 0 ? '+' : '-';
        var gmtHours = Math.abs(Math.floor(gmtOffset / 60));
        var gmtMinutes = Math.abs(gmtOffset % 60);
        var gmtZone = 'GMT ' + gmtSign + ' ' + gmtHours + ':' + (gmtMinutes < 10 ? '0' : '') + gmtMinutes;

        utilities.showLoader();
        utilities.hideButton();

        vm.currentList = [];
        vm.upcomingList = [];
        vm.pastList = [];
        vm.searchTitle = [];
        vm.selecteddomain = [];
        vm.selectedHostTeam = '';
        vm.sortByTeam = '';
        vm.host_team_choices = [];
        vm.filterStartDate = null;
        vm.filterEndDate = null;
        vm.noneCurrentChallenge = false;
        vm.noneUpcomingChallenge = false;
        vm.nonePastChallenge = false;


        vm.getAllResults = function (parameters, resultsArray, typ) {
            parameters.callback = {
                onSuccess: function (response) {
                    var data = response.data;
                    var results = data.results;

                    var timezone = moment.tz.guess();
                    for (var i in results) {

                        var descLength = results[i].description.length;
                        if (descLength >= 50) {
                            results[i].isLarge = "...";
                        } else {
                            results[i].isLarge = "";
                        }

                        var offset = new Date(results[i].start_date).getTimezoneOffset();
                        results[i].time_zone = moment.tz.zone(timezone).abbr(offset);
                        results[i].gmt_zone = gmtZone;

                        var id = results[i].id;
                        vm.challengeCreator[id] = results[i].creator.id;
                        utilities.storeData("challengeCreator", vm.challengeCreator);

                        resultsArray.push(results[i]);
                    }

                    // check for the next page
                    if (data.next !== null) {
                        var url = data.next;
                        var slicedUrl = url.substring(url.indexOf('challenges/challenge'), url.length);
                        parameters.url = slicedUrl;
                        vm.getAllResults(parameters, resultsArray);
                    } else {
                        utilities.hideLoader();
                        if (resultsArray.length === 0) {
                            vm[typ] = true;
                        } else {
                            vm[typ] = false;
                        }
                    }
                },
                onError: function () {
                    utilities.hideLoader();
                }
            };

            utilities.sendRequest(parameters);
        };


        vm.challengeCreator = {};
        var parameters = {};
        if (userKey) {
            parameters.token = userKey;
        } else {
            parameters.token = null;
        }

        // calls for ongoing challenges
        parameters.url = 'challenges/challenge/present/approved/public';
        parameters.method = 'GET';

        vm.getAllResults(parameters, vm.currentList, "noneCurrentChallenge");
        // calls for upcoming challenges
        parameters.url = 'challenges/challenge/future/approved/public';
        parameters.method = 'GET';

        vm.getAllResults(parameters, vm.upcomingList, "noneUpcomingChallenge");

        // calls for past challenges
        parameters.url = 'challenges/challenge/past/approved/public';
        parameters.method = 'GET';

        vm.getAllResults(parameters, vm.pastList, "nonePastChallenge");

        vm.scrollUp = function () {
            angular.element($window).bind('scroll', function () {
                if (this.pageYOffset >= 100) {
                    utilities.showButton();
                } else {
                    utilities.hideButton();
                }
            });
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

        vm.getFilteredCurrentChallenges = function () {
            let filtered = vm.currentList;
            filtered = $filter('customTitleFilter')(filtered, vm.searchTitle);
            filtered = $filter('customDomainFilter')(filtered, vm.selecteddomain);
            filtered = $filter('customHostFilter')(filtered, vm.selectedHostTeam);
            filtered = $filter('customDateRangeFilter')(filtered, vm.filterStartDate, vm.filterEndDate);
            filtered = $filter('orderByTeam')(filtered, vm.sortByTeam);
            return filtered;
        };

        vm.getFilteredUpcomingChallenges = function () {
            let filtered = vm.upcomingList;
            filtered = $filter('customTitleFilter')(filtered, vm.searchTitle);
            filtered = $filter('customDomainFilter')(filtered, vm.selecteddomain);
            filtered = $filter('customHostFilter')(filtered, vm.selectedHostTeam);
            filtered = $filter('customDateRangeFilter')(filtered, vm.filterStartDate, vm.filterEndDate);
            filtered = $filter('orderByTeam')(filtered, vm.sortByTeam);
            return filtered;
        };

        vm.getFilteredPastChallenges = function () {
            let filtered = vm.pastList;
            filtered = $filter('customTitleFilter')(filtered, vm.searchTitle);
            filtered = $filter('customDomainFilter')(filtered, vm.selecteddomain);
            filtered = $filter('customHostFilter')(filtered, vm.selectedHostTeam);
            filtered = $filter('customDateRangeFilter')(filtered, vm.filterStartDate, vm.filterEndDate);
            filtered = $filter('orderByTeam')(filtered, vm.sortByTeam);
            return filtered;
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