(function () {
    'use strict';

    angular
        .module('evalai')
        .controller('filterDialogCtrl', filterDialogCtrl);

        filterDialogCtrl.$inject = ['$scope', '$mdDialog', 'filterData'];

    function filterDialogCtrl($scope, $mdDialog, filterData) {
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
