// define filters here

// filter to get ceiling value
(function() {

    'use strict';

    angular
        .module('evalai')
        .filter('ceil', ceil);

    function ceil() {
        return function(input) {
            return Math.ceil(input);
        };
    }

})();
