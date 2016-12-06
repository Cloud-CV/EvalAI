// Invoking IIFE

(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('MainCtrl', MainCtrl);

    MainCtrl.$inject = ['utilities'];

    function MainCtrl(utilities) {

        var vm = this;

        vm.user = {};

        // get token
        var userKey = utilities.getData('userKey');

        if (userKey) {
            var parameters = {};
            parameters.url = 'auth/user/';
            parameters.method = 'GET';
            parameters.token = userKey;
            parameters.callback = {
                onSuccess: function(response, status) {
                    if (status == 200) {
                        vm.user.name = response.username;
                    }
                    else if (status == 403){
                        console.log(response);
                        vm.error = response.error;

                        // navigate to permissions denied page
                        $state.go('web.permission-denied');

                    }                    
                },
                onError: function() {

                }
            };

            utilities.sendRequest(parameters);
        }
        
    }

})();
