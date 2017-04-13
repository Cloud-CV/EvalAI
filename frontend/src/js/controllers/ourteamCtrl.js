// Invoking IIFE for our team

(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('ourTeamCtrl', ourTeamCtrl);

    ourTeamCtrl.$inject = ['utilities', '$rootScope'];

    function ourTeamCtrl(utilities, $rootScope) {
        /* jshint validthis: true */
        var vm = this;

        vm.contributor = {};
        vm.subErrors = {};

        vm.loadTeamList = function() {
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
        };

        vm.addNewContributor = function(formValid) {
            // checking whether the form is valid
            if (!formValid) {
                return;
            }
            // cleaning up error messages from the server before sending the request
            vm.subErrors.msg = "";

            var parameters = {};
            parameters.url = 'web/team/';
            parameters.method = 'POST';
            parameters.data = {
                "name": vm.contributor.name,
                "email": vm.contributor.email,
                "headshot": vm.contributor.headshot,
                "github_url": vm.contributor.github_url,
                "linkedin_url": vm.contributor.linkedin_url,
                "personal_website": vm.contributor.personal_website,
                "background_image": vm.contributor.background_image
            };

//            TODO: add headshot and background_image upload
            if (vm.contributor.headshot) {
//                vm.upload(vm.contributor.headshot);
            }
            if (vm.contributor.background_image) {
//                vm.upload(vm.contributor.background_image);
            }

            parameters.callback = {
                onSuccess: function() {
                    $rootScope.notify("success", "Contributor '" + vm.contributor.name + "' has been added successfully!");
                    // clearing the input form
                    vm.contributor = {};
                    // reloading the teams from server after a successful submission
                    vm.loadTeamList();
                },
                onError: function(response) {
                    var error = response.data;
                    if (response.status == 400) {
                        // getting the first error from the request.
                        // We get here the first value of object "error" which
                        // gives us an array. Then we get the first value of the array.
                        vm.subErrors.msg = error[Object.keys(error)[0]][0];
                    } else {
                        $rootScope.notify("error", "New contributor couldn't be created.");
                    }
                }
            };

            utilities.sendRequest(parameters);
        };

        // loading teams on page load here
        vm.loadTeamList();
    }
})();
