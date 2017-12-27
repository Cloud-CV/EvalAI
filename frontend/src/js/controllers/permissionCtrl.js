// Invoking IIFE for permission denied
(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('PermCtrl', PermCtrl);

    PermCtrl.$inject = ['utilities'];

    function PermCtrl(utilities) {
        var vm = this;

        // message for not verified users
        vm.emailError = utilities.getData('emailError');

        //user email redirect
        vm.user={};

        var userKey = utilities.getData('userKey');

        var parameters = {};
        parameters.url = 'auth/user/';
        parameters.method = 'GET';
        parameters.token = userKey;
        parameters.callback = {
            onSuccess: function(response) {
                var status = response.status;
                var result = response.data;
                vm.user = result;
            },
        };

        utilities.sendRequest(parameters);




    }

})();
