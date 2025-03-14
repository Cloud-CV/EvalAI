// Invoking IIFE
(function () {

    'use strict';

    angular
        .module('evalai')
        .controller('SubmissionFilesCtrl', SubmissionFilesCtrl);

    SubmissionFilesCtrl.$inject = ['utilities', '$rootScope', '$state', '$stateParams'];

    function SubmissionFilesCtrl(utilities, $rootScope, $state, $stateParams) {

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

        // Function to validate file format
        function validateFileFormat(file) {
            const acceptedFormats = ['text/csv'];
            if (!acceptedFormats.includes(file.type)) {
                $rootScope.notify('error', 'Invalid file format. Please upload a CSV file.');
                return false;
            }
            return true;
        }

        // Add event listener to file input
        document.getElementById('fileInput').addEventListener('change', function(event) {
            const file = event.target.files[0];
            if (!validateFileFormat(file)) {
                event.target.value = ''; // Clear the file input
            }
        });

        utilities.sendRequest(parameters);
    }
})();
