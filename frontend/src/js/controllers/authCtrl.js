// Invoking IIFE

(function(){

	'use strict';

	angular
	    .module('evalai')
	    .controller('AuthCtrl', AuthCtrl);

	AuthCtrl.$inject = ['utilities'];

    function AuthCtrl(utilities){

    	var vm = this;

		var parameters = {};
		parameters.url = 'auth/login/';
		parameters.method = 'POST';
		parameters.data = {
			"email": "Akash",
            "password": "check",
		}
		parameters.callback = {
			onSuccess: function(response){
				
				console.log(response + "sdsd");
			},
			onError : function(error){
				
			}
		};

		utilities.sendRequest(parameters);
    	
    }

})();
