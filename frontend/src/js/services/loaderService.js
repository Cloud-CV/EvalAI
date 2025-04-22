angular
    .module('evalai')
    .service('loaderService', ['$document', loaderService]);

function loaderService($document) {
    // find the loader element once at startup
    this.loaderContainer = angular.element(
        $document[0].querySelector('.circular-loader')
    );
    this.isExistLoader = false;
    this.loaderTitle   = '';

    // start loader
    this.startLoader = function(msg) {
        this.isExistLoader = true;
        this.loaderTitle   = msg;
        if (this.loaderContainer && this.loaderContainer.length) {
            this.loaderContainer.addClass('low-screen');
        }
    };

    // stop loader
    this.stopLoader = function() {
        this.isExistLoader = false;
        this.loaderTitle   = '';
        if (this.loaderContainer && this.loaderContainer.length) {
            this.loaderContainer.removeClass('low-screen');
        }
    };

    return this;
}
