
     angular
         .module('evalai')
         .service('loaderService', loaderService);

         function loaderService() {

             //start loader
             this.startExistLoader = function(msg) {
                 this.isExistLoader = true;
                 this.loaderTitle = msg;
                 this.loginContainer.addClass('low-screen');
             };

             // stop loader
             this.stopExistLoader = function() {
                 this.isExistLoader = false;
                 this.loaderTitle = '';
                 this.loginContainer.removeClass('low-screen');
             };

             return this;

         }

