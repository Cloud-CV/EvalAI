// Invoking IIFE for dashboard

<<<<<<< HEAD
(function(){

	'use strict';

	angular
	    .module('evalai')
	    .controller('WebCtrl', WebCtrl);

	WebCtrl.$inject = ['utilities', '$state'];

    function WebCtrl(utilities, $state){
    	var vm = this;
    	
    	// vm.name = "check"				
=======
(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('WebCtrl', WebCtrl);

    WebCtrl.$inject = ['utilities', '$state', '$stateParams'];

    function WebCtrl(utilities, $state, $stateParams) {
        var vm = this;

        vm.user = {};
        vm.countLeft = 0;
        vm.compPerc = 0;
        var count = 0;

        // added sidebar box-shadow on scroll
        angular.element().find(".side-intro").addClass("z-depth-3");

        // get token
        var userKey = utilities.getData('userKey');

        var parameters = {};
        parameters.url = 'auth/user/';
        parameters.method = 'GET';
        parameters.token = userKey;
        parameters.callback = {
            onSuccess: function(response, status) {
                if (status == 200) {
                    vm.name = response.username;

                    for (var i in response) {
                        if (response[i] == "" || response[i] == undefined || response[i] == null) {
                            response[i] = "-";
                            vm.countLeft = vm.countLeft + 1;
                        }
                        count = count + 1;
                    }
                    vm.compPerc = parseInt((vm.countLeft / count) * 100);

                    vm.user = response;
                    vm.user.complete = 100 - vm.compPerc;

                }
            },
            onError: function() {

            }
        };

        utilities.sendRequest(parameters);

        // vm.name = "check"				
>>>>>>> aj-dashboard-old-copy
    }

})();
