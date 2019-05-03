// Invoking IIFE
(function () {

    'use strict';

    angular
        .module('evalai')
        .controller('SubmissionFilesCtrl', SubmissionFilesCtrl);

    SubmissionFilesCtrl.$inject = ['utilities', 'loaderService', '$scope', '$rootScope', '$state', '$http', '$stateParams'];

    function SubmissionFilesCtrl(utilities, loaderService, $scope, $rootScope, $state, $http, $stateParams) {

        var vm = this;
        vm.bucket = $stateParams.bucket;
        vm.key = $stateParams.key;
        var userKey = utilities.getData('userKey');
        var parameters = {};
        parameters.url = 'jobs/submission_files/?bucket=' + vm.bucket + '&key=' + vm.key;
        parameters.method = 'GET';
        parameters.token = userKey;
        parameters.callback = {
            onSuccess: function (response) {
                vm.data = response.data;
                var status = response.status;
                if (status === 200) {
                    window.location.href = vm.data.signed_url;
                } else {
                    $state.go('error-404');
                }
            },
            onError: function (response) {
                vm.data = response.data;
                $state.go('error-404');
                $rootScope.notify('error', vm.data.error);
            }
        };
        utilities.sendRequest(parameters);
    }
})();
