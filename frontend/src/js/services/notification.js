(function() {

    'use strict';

    angular
        .module('evalai')
        .service('evNotifyMsg', evNotifyMsg);


    function evNotifyMsg() {
        // factory for notification generator

        this.launch = function(msg) {
            var notifyMsg = msg;
            return notifyMsg;
        };
    }

})();
