// Invoking IIFE

(function(){

	'use strict';

	angular
    .module('evalai')
    .controller('MainCtrl', MainCtrl);

    function MainCtrl (){

    	var vm =this;

    	vm.check = "HI there!";
    }

})();
