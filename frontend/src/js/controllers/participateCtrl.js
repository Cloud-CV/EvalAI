(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('ParticipateCtrl', ParticipateCtrl);

    ParticipateCtrl.$inject = ['utilities', 'loaderService', '$scope', '$state', '$http', '$rootScope', '$mdDialog'];

    function ParticipateCtrl(utilities, loaderService, $scope, $state) {
        var userKey = utilities.getData('userKey');
        var parameters = {};
        parameters.url = 'challenges/participate/';
        parameters.method = 'GET';
        if (userKey) {
            parameters.token = userKey;
        }
        parameters.callback = {
            onError: function(response) {
                var error = response.data;
                utilities.storeData('emailError', error.detail);
                document.getElementById("showonVerified").style.display = 'none';
                document.getElementById("showonUnverified").style.display = 'block';
                utilities.hideLoader();
            }
        };
        utilities.sendRequest(parameters);
    }
})();
