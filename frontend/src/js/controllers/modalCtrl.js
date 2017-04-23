(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('modalCtrl', modalCtrl);

    modalCtrl.$inject = ['utilities', '$state', '$http', '$rootScope', 'close'];

    function modalCtrl(utilities, $state, $http, $rootScope, close) {
        var vm = this;
        vm.close = close;
    }
})();
