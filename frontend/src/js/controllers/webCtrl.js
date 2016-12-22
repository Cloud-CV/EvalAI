// Invoking IIFE for dashboard
(function() {

    'use strict';

    angular
        .module('evalai')
        .controller('WebCtrl', WebCtrl);

    WebCtrl.$inject = ['utilities', '$state', '$stateParams', '$rootScope'];

    function WebCtrl(utilities, $state, $stateParams, $rootScope) {
        var vm = this;

        vm.user = {};
        vm.countLeft = 0;
        vm.compPerc = 0;
        var count = 0;

        utilities.hideLoader();

        // $rootScope.loaderTitle = '';
        // vm.loginContainer = angular.element('.web-container');

        // // show loader
        // vm.startLoader = function(msg) {
        //     $rootScope.isLoader = true;
        //     $rootScope.loaderTitle = msg;
        //     vm.loginContainer.addClass('low-screen');
        // }

        // // stop loader
        // vm.stopLoader = function() {
        //     $rootScope.isLoader = false;
        //     $rootScope.loaderTitle = '';
        //     vm.loginContainer.removeClass('low-screen');
        // }

        // added sidebar box-shadow on scroll
        angular.element().find(".side-intro").addClass("z-depth-3");

        // get token
        var userKey = utilities.getData('userKey');

        var parameters = {};
        parameters.url = 'auth/user/';
        parameters.method = 'GET';
        parameters.token = userKey;
        parameters.callback = {
            onSuccess: function(response, status) {
                if (status == 200) {
                    vm.name = response.username;

                    for (var i in response) {
                        if (response[i] == "" || response[i] == undefined || response[i] == null) {
                            response[i] = "-";
                            vm.countLeft = vm.countLeft + 1;
                        }
                        count = count + 1;
                    }
                    vm.compPerc = parseInt((vm.countLeft / count) * 100);

                    vm.user = response;
                    vm.user.complete = 100 - vm.compPerc;

                }
            },
            onError: function(error, status) {
                alert("")
            }
        };

        utilities.sendRequest(parameters);

    }

})();
