// define services here
(function (){

	'use strict';

	angular
		.module('evalai')
		.service('utilities', utilities);

	utilities.$inject = ['$http'];

	function utilities ($http){
		

		// factory for API calls
		this.sendRequest = function(parameters){
			var url='http://localhost:8000/api/' + parameters.url;
			var data = parameters.data;
			var token = parameters.token;
			var method = parameters.method;
			var success = parameters.callback.onSuccess;
			var error = parameters.callback.onError;
			var headers = {
					'Authorization': "Token "+token
				};

			if (method == "POST") {
		        var req = {
		            method: parameters.method,
		            url: url,
		            data: data,
		            headers: headers
		        };
		    } else if (method == "GET") {
		        var req = {
		            method: parameters.method,
		            url: url,
		            headers: headers
		        };
		    }else if (method == "PUT") {
		        var req = {
		            method: parameters.method,
		            url: url,
		            data: data,
		            headers: headers
		        };
		    }
		    req.timeout = 6000;
	    
		    $http(req)
		    	.success(success)
		    	.error(error);
		}
	}

})();
