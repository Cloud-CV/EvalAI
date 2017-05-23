
     angular
         .module('evalai')
         .service('loaderService', loaderService);

         function loaderService() {

             //start loader
             this.startLoader = function(msg) {
                 this.isExistLoader = true;
                 this.loaderTitle = msg;
                 this.loaderContainer.addClass('low-screen');
             };

             // stop loader
             this.stopLoader = function() {
                 this.isExistLoader = false;
                 this.loaderTitle = '';
                 this.loaderContainer.removeClass('low-screen');
             };

             return this;

         }

