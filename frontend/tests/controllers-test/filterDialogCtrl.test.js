'use strict';

describe('filterDialogCtrl', function () {
    var $controller, $scope, $mdDialog, filterData;

    beforeEach(angular.mock.module('evalai'));

    beforeEach(inject(function (_$controller_, _$rootScope_, _$mdDialog_) {
        $controller = _$controller_;
        $scope = _$rootScope_.$new();
        $mdDialog = _$mdDialog_;
        spyOn($mdDialog, 'hide');
        spyOn($mdDialog, 'cancel');
    }));

    it('should initialize $scope variables from complete filterData', function () {
        filterData = {
            selecteddomain: ['Computer Vision'],
            selectedHostTeam: 'Team A',
            sortByTeam: 'asc',
            filterStartDate: new Date('2023-01-01'),
            filterEndDate: new Date('2023-12-31'),
            domain_choices: [['All', 'All'], ['Computer Vision', 'Computer Vision']],
            host_team_choices: ['Team A', 'Team B']
        };

        $controller('filterDialogCtrl', {
            $scope: $scope,
            $mdDialog: $mdDialog,
            filterData: filterData
        });

        expect($scope.selecteddomain).toEqual(['Computer Vision']);
        expect($scope.selectedHostTeam).toBe('Team A');
        expect($scope.sortByTeam).toBe('asc');
        expect($scope.filterStartDate).toEqual(new Date('2023-01-01'));
        expect($scope.filterEndDate).toEqual(new Date('2023-12-31'));
        expect($scope.domain_choices).toEqual([['All', 'All'], ['Computer Vision', 'Computer Vision']]);
        expect($scope.host_team_choices).toEqual(['Team A', 'Team B']);
    });

    it('should initialize $scope variables when some filterData properties are undefined', function () {
        filterData = {
            selecteddomain: undefined,
            selectedHostTeam: null,
            sortByTeam: 'asc',
           
            domain_choices: [['All', 'All']],
            host_team_choices: []
        };

        $controller('filterDialogCtrl', {
            $scope: $scope,
            $mdDialog: $mdDialog,
            filterData: filterData
        });

        expect($scope.selecteddomain).toBeUndefined();
        expect($scope.selectedHostTeam).toBeNull();
        expect($scope.sortByTeam).toBe('asc');
        expect($scope.filterStartDate).toBeUndefined();
        expect($scope.filterEndDate).toBeUndefined();
        expect($scope.domain_choices).toEqual([['All', 'All']]);
        expect($scope.host_team_choices).toEqual([]);
    });

    it('should call $mdDialog.hide with correct data on apply()', function () {
        filterData = {
            selecteddomain: ['Computer Vision'],
            selectedHostTeam: 'Team A',
            sortByTeam: 'asc',
            filterStartDate: new Date('2023-01-01'),
            filterEndDate: new Date('2023-12-31'),
            domain_choices: [['All', 'All']],
            host_team_choices: ['Team A']
        };
        $controller('filterDialogCtrl', {
            $scope: $scope,
            $mdDialog: $mdDialog,
            filterData: filterData
        });

        
        $scope.selecteddomain = ['NLP'];
        $scope.selectedHostTeam = 'Team B';
        $scope.sortByTeam = 'desc';
        $scope.filterStartDate = new Date('2024-01-01');
        $scope.filterEndDate = new Date('2024-12-31');

        $scope.apply();

        expect($mdDialog.hide).toHaveBeenCalledWith({
            selecteddomain: ['NLP'],
            selectedHostTeam: 'Team B',
            sortByTeam: 'desc',
            filterStartDate: new Date('2024-01-01'),
            filterEndDate: new Date('2024-12-31')
        });
    });

    it('should call $mdDialog.cancel on cancel()', function () {
        filterData = {};
        $controller('filterDialogCtrl', {
            $scope: $scope,
            $mdDialog: $mdDialog,
            filterData: filterData
        });
        $scope.cancel();
        expect($mdDialog.cancel).toHaveBeenCalled();
    });
});