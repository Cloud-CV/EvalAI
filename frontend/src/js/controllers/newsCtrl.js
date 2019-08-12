// Invoking IIFE for news

(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('newsCtrl', newsCtrl);

    newsCtrl.$inject = ['utilities'];

    function newsCtrl(utilities) {
        var vm = this;

        // To get the previous profile data
        var parameters = {};
        parameters.url = 'web/news/';
        parameters.method = 'GET';
        parameters.callback = {
            onSuccess: function(response) {
                var status = response.status;
                var result = response.data;
                if (status == 200) {
                    vm.news = result;
                }
            },
            onError: function() {}
        };

        utilities.sendRequest(parameters);
    }

})();
