// define directives here

(function(){

	'use strict'

	// dynamic header directive
	angular
		.module('evalai')
		.directive('dynHeader', dynHeader);

	function dynHeader(){
		var directive = {
			link: link,
			templateUrl: 'dist/views/web/partials/dyn-header.html',
			restrict: 'EA'
		};
		return directive;

		function link(scope, element, attrs){
			
			function headerComp (){
				var self = this;
				this.init();
			};

			headerComp.prototype = {
				init: function  () {
					var self =this;

					// initialized mobile sidebar
					angular.element(".button-collapse").sideNav({
						menuWidth: 200, 
						closeOnClick: true,
						draggable: true
					});

				}
			};

			var headerObj = new headerComp();
		}
	}

})();
