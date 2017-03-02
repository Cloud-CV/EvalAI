// Invoking IIFE for our team

(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('ourTeamCtrl', ourTeamCtrl);

    ourTeamCtrl.$inject = ['utilities', '$state', '$rootScope', '$mdDialog'];

    function ourTeamCtrl(utilities, $state, $rootScope, $mdDialog) {
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
                }
            }
        };

        utilities.sendRequest(parameters, "no-header");
    }
})();
