// Invoking IIFE for dashboard

(function(){

	'use strict';

	angular
	    .module('evalai')
	    .controller('WebCtrl', WebCtrl);

	WebCtrl.$inject = ['utilities', '$state'];

    function WebCtrl(utilities, $state){
    	var vm = this;
    	
    	// vm.name = "check"				
    }

})();
