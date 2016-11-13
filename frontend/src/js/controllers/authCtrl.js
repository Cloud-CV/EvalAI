// Invoking IIFE

(function(){

	'use strict';

	angular
    .module('evalai')
    .controller('AuthCtrl', AuthCtrl);

    function AuthCtrl (){

    	var vm =this;
    	
    	vm.check = "Login UI"
    }

})();
