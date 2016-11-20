// Invoking IIFE for dashboard

(function(){

	'use strict';

	angular
	    .module('evalai')
	    .controller('DashCtrl', DashCtrl);

	DashCtrl.$inject = ['utilities', '$state'];

    function DashCtrl(utilities, $state){
    	var vm = this;
    	
    	// get token
    	var userKey = utilities.getData('userKey');
    		userKey = userKey.key;

    	var parameters = {};
			parameters.url = 'auth/user/';
			parameters.method = 'GET';
			parameters.token = userKey;
			parameters.callback = {
				onSuccess: function(response, status){
					if(status == 200){
						vm.name = response.username;
					}
				},
				onError: function(){

				}
			};

			utilities.sendRequest(parameters);				
    }

})();
