// Invoking IIFE for challenge page
(function() {

    'use strict';
    angular
        .module('evalai')
        .controller('ChallengeListCtrl', ChallengeListCtrl);

    ChallengeListCtrl.$inject = ['utilities', '$window', '$scope', '$interval'];

    function ChallengeListCtrl(utilities, $window, $scope, $interval) {
        var vm = this;
        var userKey = utilities.getData('userKey');

        utilities.showLoader();

        vm.currentList = {};
        vm.upcomingList = {};
        vm.pastList = {};

        vm.noneCurrentChallenge = false;
        vm.noneUpcomingChallenge = false;
        vm.nonePastChallenge = false;
        

//         // Set the date we're counting down to
// var countDownDate = new Date("Jan 5, 2021 15:37:25").getTime();

// // Update the count down every 1 second
// var x = $interval(function() {
//   // Get todays date and time
//   var now = new Date().getTime();
    
//   // Find the distance between now and the count down date
//   var distance = countDownDate - now;
    
//   // Time calculations for days, hours, minutes and seconds
//   var days = Math.floor(distance / (1000 * 60 * 60 * 24));
//   var hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
//   var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
//   var seconds = Math.floor((distance % (1000 * 60)) / 1000);
    
//   // Output the result in an element with id="demo"
//   $scope.countdown = days + "d " + hours + "h "
//   + minutes + "m " + seconds + "s ";
    
//   // If the count down is over, write some text 
//   if (distance < 0) {
//     clearInterval(x);
//     $scope.countdown = "EXPIRED";
//   }
// }, 1000);

        // calls for ongoing challneges
        vm.challengeCreator = {};
        var parameters = {};
        parameters.method = 'GET';
        if (userKey) {
            parameters.token = userKey;
        } else {
            parameters.token = null;
        }
        parameters.url = 'challenges/challenge/present';

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
                    // var end_time = new Date(vm.currentList[i].end_date).getTime();
                    // var now = new Date().getTime();
                    // var one_month_time = 30 * 60 * 60 * 24;
                    // var difference = end_time - now;
                    // var remaining_seconds = difference % (1000 * 60) / 1000;
                    // if (remaining_seconds <= one_month_time) {
                    //     // Update the count down every 1 second
                    //     $interval(function() {
                    //         var days = Math.floor(difference / (1000 * 60 * 60 * 24));
                    //         var hours = Math.floor((difference % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                    //         var minutes = Math.floor((difference % (1000 * 60 * 60)) / (1000 * 60));
                    //         var seconds = Math.floor((difference % (1000 * 60)) / 1000);

                    //         $scope.countdown = days + "d " + hours + "h "
                    //         + minutes + "m " + seconds + "s ";

                    //         if (remaining_seconds < 0) {
                    //             $scope.countdown = "Closed";
                    //         }
                    //     }, 1000);
                    // }

                    var descLength = vm.currentList[i].description.length;
                    if (descLength >= 50) {
                        vm.currentList[i].isLarge = "...";
                    } else {
                        vm.currentList[i].isLarge = "";
                    }

                    var id = vm.currentList[i].id;
                    vm.challengeCreator[id] = vm.currentList[i].creator.id;
                    utilities.storeData("challengeCreator", vm.challengeCreator);
                }

                // dependent api
                // calls for upcoming challneges
                parameters.url = 'challenges/challenge/future';
                parameters.method = 'GET';

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

                        // dependent api
                        // calls for upcoming challneges
                        parameters.url = 'challenges/challenge/past';
                        parameters.method = 'GET';

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
                                    vm.challengeCreator[id] = vm.pastList[i].creator.id;
                                    utilities.storeData("challengeCreator", vm.challengeCreator);
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
            angular.element($window).bind('scroll', function() {
                if (this.pageYoffset >= 100) {
                    utilities.showButton();
                } else {
                    utilities.hideButton();
                }
            });
        };
    }

})();
