// Invoking IIFE for challenge page
(function() {

    'use strict';
    angular
        .module('evalai')
        .controller('ChallengeListCtrl', ChallengeListCtrl);

    ChallengeListCtrl.$inject = ['utilities', '$window', '$http'];

    function ChallengeListCtrl(utilities, $window, $http) {
        var vm = this;
        var userKey = utilities.getData('userKey');

        utilities.showLoader();

        // default variables/objects
        vm.existTeam = {};
        vm.currentPage = '';
        vm.isNext = '';
        vm.isPrev = '';
        vm.showPagination = false;

        // calls for ongoing challneges
        vm.challengeCreator = {};
        var parameters = {};
        parameters.url = 'challenges/challenge/present';
        parameters.method = 'GET';
        parameters.token = userKey;

        parameters.callback = {
            onSuccess: function(response) {
                var status= response.status;
                var data = response.data;
                vm.currentList = data.results;

                if(status=200){
                  vm.existList=data;
                  if (vm.existList.count === 0) {
                        vm.showPagination = false;
                        vm.paginationMsg = "No team exists for now, start by creating a new team!";
                    } else {
                        vm.showPagination = true;
                        vm.paginationMsg = "";
                    }
                    // condition for pagination
                    if (vm.existList.next === null) {
                        vm.isNext = 'disabled';
                    } else {
                        vm.isNext = '';
                    }

                    if (vm.existList.previous === null) {
                        vm.isPrev = 'disabled';
                    } else {
                        vm.isPrev = '';
                    }
                    if (vm.existList.next !== null) {
                        vm.currentPage = vm.existList.next.split('page=')[1] - 1;
                    } else {
                        vm.currentPage = 1;
                    }
                    vm.load=function(url){

                        if (url !== null) {

                            console.log(url);
                            //store the header data in a variable
                            var headers = {
                                'Authorization': "Token " + userKey
                            };

                            //Add headers with in your request
                            $http.get(url, { headers: headers }).then(function(response) {
                                // reinitialized data
                                var details = response.data;
                                vm.existList = details;

                                // condition for pagination
                                if (vm.existList.next === null) {
                                    vm.isNext = 'disabled';
                                    vm.currentPage = vm.existList.count / 10;
                                } else {
                                    vm.isNext = '';
                                    vm.currentPage = parseInt(vm.existList.next.split('page=')[1] - 1);
                                }
                                if (vm.existList.previous === null) {
                                    vm.isPrev = 'disabled';
                                } else {
                                    vm.isPrev = '';
                                }
                            });
                       }
                     };

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

                            var id = vm.upcomingList[i].id;              
                            vm.challengeCreator[id] = vm.upcomingList[i].creator.id;
                            utilities.storeData("challengeCreator", vm.challengeCreator);
                        }

                        if(vm.upcomingList.length !=0){
                             vm.futureLoadIndex=3;
                             vm.showMore = function() {
                                if (vm.futureLoadIndex < vm.upcomingList.length){
                                   vm.futureLoadIndex = vm.futureLoadIndex+1;
                                }
                             };
                             vm.showLess = function() {
                                if (vm.futureLoadIndex > 3){
                                   vm.futureLoadIndex = vm.futureLoadIndex-1;
                                }
                             };
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
                                    var id = vm.pastList[i].id;              
                                    vm.challengeCreator[id]= vm.pastList[i].creator.id;
                                    utilities.storeData("challengeCreator", vm.challengeCreator);
                                }

                                if(vm.pastList.length !=0){
                                    vm.pastLoadIndex=3;
                                      vm.showMore = function() {
                                        if (vm.pastLoadIndex < vm.pastList.length){
                                           vm.pastLoadIndex = vm.pastLoadIndex+1;
                                        }
                                     };
                                     vm.showLess = function() {
                                        if (vm.pastLoadIndex > 3){
                                           vm.pastLoadIndex = vm.pastLoadIndex-1;
                                        }
                                     };
                                }

                                utilities.hideLoader();

                            },
                            onError: function() {
                                utilities.hideLoader();
                            }
                        };

                        utilities.sendRequest(parameters);

                    },
                    onError: function() {
                        utilities.hideLoader();
                    }
                };

                utilities.sendRequest(parameters);

            },
            onError: function() {

                utilities.hideLoader();
            }
        };

        utilities.sendRequest(parameters);

        vm.scrollUp = function() { 
            utilities.hideButton();
            angular.element($window).bind('scroll', function(){
                if(this.pageYoffset >= 100 ){
                     utilities.showButton();
                }else{
                     utilities.hideButton();
                }
            });
        };

        // utilities.showLoader();
    }

})();
