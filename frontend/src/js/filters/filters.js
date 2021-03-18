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

    angular.module('evalai')
            .filter('format_execution_time', format_execution_time);

    function format_execution_time() {
        return function(execution_time) {
            var executiontime = new Date(execution_time * 1000);
            var days = (executiontime.getUTCDate() - 1);
            var hours = executiontime.getUTCHours();
            var minutes = executiontime.getUTCMinutes();
            var seconds = executiontime.getSeconds();
            var timeString = (days != 0 ? days.toString().padStart(2, '0') + ' day ' : '') + (hours != 0 ? hours.toString().padStart(2, '0') + ' hr ' : '')+ 
                (minutes != 0 ? minutes.toString().padStart(2, '0') + ' min ' : '') + 
                seconds.toString().padStart(2, '0') + ' sec';
            return timeString;
        };
    }

})();
