// Invoking IIFE for challenge page
(function() {

    'use strict';
    angular
        .module('evalai')
        .controller('ChallengeListCtrl', ChallengeListCtrl);

    ChallengeListCtrl.$inject = ['utilities', '$state', '$stateParams', '$rootScope'];

    function ChallengeListCtrl(utilities, $state, $stateParams, $rootScope) {
        var vm = this;
        var userKey = utilities.getData('userKey');

        utilities.showLoader();

        vm.imgUrlObj = {
            ironman: "dist/images/ironman.png",
            hulk: "dist/images/hulk.png",
            women: "dist/images/women.png",
            bird: "dist/images/bird.png",
            captain: "dist/images/captain.png"
        };

        vm.currentList = {};
        vm.upcomingList = {};
        vm.pastList = {};

        vm.noneCurrentChallenge = false;
        vm.noneUpcomingChallenge = false;
        vm.nonePastChallenge = false;

        // calls for ongoing challneges
        var parameters = {};
        parameters.url = 'challenges/challenge/present';
        parameters.method = 'GET';
        parameters.token = userKey;

        parameters.callback = {
            onSuccess: function(response) {
                var data = response.data;
                vm.currentList = data.results;

                if (vm.currentList.length === 0) {
                    vm.noneCurrentChallenge = true;
                } else {
                    vm.noneCurrentChallenge = false;
                }

                for (var i in vm.currentList) {

                    var descLength = vm.currentList[i].description.length;
                    if (descLength >= 50) {
                        vm.currentList[i].isLarge = "...";
                    } else {
                        vm.currentList[i].isLarge = "";
                    }

                    if (vm.currentList[i].background_image === undefined || vm.currentList[i].background_image === null) {
                        vm.currentList[i].background_image = vm.imgUrlObj.hulk;
                    }


                }

                // dependent api
                // calls for upcoming challneges
                var parameters = {};
                parameters.url = 'challenges/challenge/future';
                parameters.method = 'GET';
                parameters.token = userKey;

                parameters.callback = {
                    onSuccess: function(response) {
                        var data = response.data;
                        vm.upcomingList = data.results;

                        if (vm.upcomingList.length === 0) {
                            vm.noneUpcomingChallenge = true;
                        } else {
                            vm.noneUpcomingChallenge = false;
                        }

                        for (var i in vm.upcomingList) {

                            var descLength = vm.upcomingList[i].description.length;

                            if (descLength >= 50) {
                                vm.upcomingList[i].isLarge = "...";
                            } else {
                                vm.upcomingList[i].isLarge = "";
                            }

                            if (vm.upcomingList[i].background_image === undefined || vm.upcomingList[i].background_image === null) {
                                vm.upcomingList[i].background_image = vm.imgUrlObj.captain;
                            }
                        }

                        // dependent api
                        // calls for upcoming challneges
                        var parameters = {};
                        parameters.url = 'challenges/challenge/past';
                        parameters.method = 'GET';
                        parameters.token = userKey;

                        parameters.callback = {
                            onSuccess: function(response) {
                                var data = response.data;
                                vm.pastList = data.results;

                                if (vm.pastList.length === 0) {
                                    vm.nonePastChallenge = true;
                                } else {
                                    vm.nonePastChallenge = false;
                                }


                                for (var i in vm.pastList) {


                                    var descLength = vm.pastList[i].description.length;
                                    if (descLength >= 50) {
                                        vm.pastList[i].isLarge = "...";
                                    } else {
                                        vm.pastList[i].isLarge = "";
                                    }
                                    if (vm.pastList[i].background_image === undefined || vm.pastList[i].background_image === null) {

                                        vm.pastList[i].background_image = vm.imgUrlObj.bird;
                                    }
                                }

                                utilities.hideLoader();

                            },
                            onError: function(response) {
                                utilities.hideLoader();
                            }
                        };

                        utilities.sendRequest(parameters);

                    },
                    onError: function(response) {
                        utilities.hideLoader();
                    }
                };

                utilities.sendRequest(parameters);

            },
            onError: function(response) {

                utilities.hideLoader();
            }
        };

        utilities.sendRequest(parameters);



        // utilities.showLoader();
    }

})();
