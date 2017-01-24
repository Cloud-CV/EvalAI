// define filters here

// filter to get ceiling value
(function() {

    'use strict'

    angular
        .module('evalai')
        .filter('ceil', ceil)
        .filter('numKeys', numKeys);

    function ceil() {
        return function(input) {
            return Math.ceil(input);
        };
    }

    function numKeys() {
        return function(json) {
            var keys = Object.keys(json)
            return keys.length;
        }
    }

})();
