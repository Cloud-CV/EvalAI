// (function() {

//     'use strict';

//     angular
//         .module('evalai')
//         .controller('ParticipateCtrl', ParticipateCtrl);

//     ParticipateCtrl.$inject = ['utilities', 'loaderService', '$scope', '$state', '$http', '$rootScope', '$mdDialog','$stateParams'];

//     function ParticipateCtrl(utilities, loaderService, $scope, $state,$stateParams) {
//         var vm = this;
        
//         vm.challengeId = $stateParams.challengeId;
//         var userKey = utilities.getData('userKey');
//         var parameters = {};
//         parameters.url = 'participants/participant_teams/challenges/';
//         parameters.method = 'GET';
//         if (userKey) {
//             parameters.token = userKey;
//         }
//         parameters.callback = {
//             onError: function(response) {
//                 var error = response.data;
//                 utilities.storeData('emailError', error.detail);
//                 document.getElementById("showonVerified").style.display = 'none';
//                 document.getElementById("showonUnverified").style.display = 'block';
//                 utilities.hideLoader();
//             }
//         };
//         utilities.sendRequest(parameters);
//     }
// })();
