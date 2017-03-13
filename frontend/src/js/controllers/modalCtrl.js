(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('modalCtrl', modalcont);

    modalcont.$inject = ['utilities', '$state', '$http', '$rootScope', 'close'];

    function modalcont(utilities, $state, $http, $rootScope, close) {
        var vm = this;
        vm.close = close;
    }
})();
