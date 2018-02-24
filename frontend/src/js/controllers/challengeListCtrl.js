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
        vm.existList = {};
        vm.currentPage = '';
        vm.isNext = '';
        vm.isPrev = '';
        vm.showPagination = false;
        vm.upcomingList = {};
        vm.currentPageFuture = '';
        vm.isNextFuture = '';
        vm.isPrevFuture = '';
        vm.showPaginationFuture = false;
        vm.pastList = {};
        vm.currentPagePast = '';
        vm.isNextPast = '';
        vm.isPrevPast = '';
        vm.showPaginationPast = false;

        // calls for ongoing challneges
        vm.challengeCreator = {};
        var parameters = {};
        parameters.url = 'challenges/challenge/present';
        parameters.method = 'GET';
        parameters.token = userKey;

        parameters.callback = {
            onSuccess: function(response) {
                var data = response.data;

                  vm.existList=data;
                    if (vm.existList.count === 0) {
                        vm.showPagination = false;
                    } else {
                        vm.showPagination = true;
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
                        vm.currentPage = vm.currentList.next.split('page=')[1] - 1;
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
                                vm.currentList = details;

                                // condition for pagination
                                if (vm.currentList.next === null) {
                                    vm.isNext = 'disabled';
                                    vm.currentPage = vm.existList.count / 10;
                                } else {
                                    vm.isNext = '';
                                    vm.currentPage = parseInt(vm.existList.next.split('page=')[1] - 1);
                                }
                                if (vm.currentList.previous === null) {
                                    vm.isPrev = 'disabled';
                                } else {
                                    vm.isPrev = '';
                                }
                            });
                       }
                     };

                    // dependent api
                    // calls for upcoming challneges
                    var parameters = {};
                    parameters.url = 'challenges/challenge/future';
                    parameters.method = 'GET';
                    parameters.token = userKey;

                    parameters.callback = {
                        onSuccess: function(response) {
                            var data = response.data;
                            vm.upcomingList= data;
                            console.log('aoo');
                            console.log(vm.upcomingList);                        

                            if(vm.upcomingList.count===0){
                               vm.showPaginationFuture=false;
                            }else{
                               vm.showPaginationFuture = true;
                            }
                            if (vm.upcomingList.previous === null) {
                               vm.isPrevFuture = 'disabled';
                            } else {
                               vm.isPrevFuture = '';
                            }
                            if (vm.upcomingList.next !== null) {
                               vm.currentPageFuture = vm.upcomingList.next.split('page=')[1] - 1;
                            } else {
                               vm.currentPageFuture = 1;
                            }
                            // to load data with pagination
                            vm.load = function(url){
                               vm.isExistLoader = true;
                               vm.loaderTitle = '';
                               vm.loaderContainer = angular.element('.exist-team-card');
                               if (url !== null) {
                                   //store the header data in a variable
                                   var headers = {
                                     'Authorization': "Token " + userKey
                                   };
                                   //Add headers with in your request
                                     $http.get(url, { headers: headers }).then(function(response){
                                     // reinitialized data
                                     var details = response.data;
                                     vm.upcomingList = details;
                                     // condition for pagination
                                     if (vm.upcomingList.next === null) {
                                         vm.isNextFuture = 'disabled';
                                         vm.currentPageFuture = vm.upcomingList.count / 10;
                                     } else {
                                         vm.isNextFuture = '';
                                         vm.currentPageFuture = parseInt(vm.upcomingList.next.split('page=')[1] - 1);
                                     }
                                     if (vm.upcomingList.previous === null) {
                                          vm.isPrevFuture = 'disabled';
                                     } else {
                                          vm.isPrevFuture = '';
                                     }
                                   });
                               }
                            };


                        // dependent api
                        // calls for upcoming challneges
                        var parameters = {};
                        parameters.url = 'challenges/challenge/past';
                        parameters.method = 'GET';
                        parameters.token = userKey;

                        parameters.callback = {
                            onSuccess: function(response) {
                                var data = response.data;
                                vm.pastList = data;

                                console.log(vm.pastList);

                                if (vm.pastList.count === 0) {
                                    vm.showPaginationPast = false;
                                } else {
                                    vm.showPaginationPast = true;
                                }
                                // condition for pagination
                                if (vm.pastList.next === null) {
                                    vm.isNextPast = 'disabled';
                                } else {
                                    vm.isNextPast = '';
                                }
                                if (vm.pastList.previous === null) {
                                    vm.isPrevPast = 'disabled';
                                } else {
                                    vm.isPrevPast = '';
                                }
                                if (vm.pastList.next !== null) {
                                    vm.currentPagePast = vm.pastList.next.split('page=')[1] - 1;
                                } else {
                                    vm.currentPagePast = 1;
                                }

                                // to load data with pagination
                                vm.load = function(url) {
                                   vm.isExistLoader = true;
                                   vm.loaderTitle = '';
                                   vm.loaderContainer = angular.element('.exist-team-card');


                                if (url !== null) {

                                    //store the header data in a variable
                                    var headers = {
                                        'Authorization': "Token " + userKey
                                    };

                                    //Add headers with in your request
                                    $http.get(url, { headers: headers }).then(function(response) {
                                      // reinitialized data
                                      var details = response.data;
                                      vm.pastList = details;

                                      // condition for pagination
                                      if (vm.pastList.next === null) {
                                         vm.isNextPast = 'disabled';
                                         vm.currentPagePast = vm.pastList.count / 10;
                                      } else {
                                         vm.isNextPast = '';
                                         vm.currentPagePast = parseInt(vm.pastList.next.split('page=')[1] - 1);
                                      }
                                      if (vm.pastList.previous === null) {
                                          vm.isPrevPast = 'disabled';
                                      } else {
                                          vm.isPrevPast = '';
                                      }
                                    });
                                }		    
                              };

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
