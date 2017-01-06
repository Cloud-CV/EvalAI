// define services here

// Basic utilities
(function() {

    'use strict';

    angular
        .module('evalai')
        .service('utilities', utilities);

    utilities.$inject = ['$http', 'EnvironmentConfig', '$rootScope'];

    function utilities($http, EnvironmentConfig, $rootScope) {

        // factory for API calls
        this.sendRequest = function(parameters, header) {
            var url = EnvironmentConfig.API + parameters.url;
            var data = parameters.data;
            var token = parameters.token;
            var method = parameters.method;
            var successCallback = parameters.callback.onSuccess;
            var errorCallback = parameters.callback.onError;
            // alert(EnvironmentConfig.API)
            var headers = {
                'Authorization': "Token " + token
            };

            // function to check for applying header
            function pick(arg, def) {
                return (typeof arg == 'undefined' ? def : arg);
            };

            header = pick(header, 'header');

            if (method == "POST" && header == 'header') {
                var req = {
                    method: parameters.method,
                    url: url,
                    data: data,
                    headers: headers
                };
            } else if (method == "POST" && header == 'no-header') {
                var req = {
                    method: parameters.method,
                    url: url,
                    data: data
                };
            } else if (method == "GET") {
                var req = {
                    method: parameters.method,
                    url: url,
                    headers: headers
                };
            } else if (method == "PUT") {
                var req = {
                    method: parameters.method,
                    url: url,
                    data: data,
                    headers: headers
                };
            } else if (method == "DELETE") {
                var req = {
                    method: parameters.method,
                    url: url,
                    headers: headers
                };
            }

            req.timeout = 6000;

            $http(req)
                .then(successCallback, errorCallback);
        };

        this.storeData = function(key, value) {
            localStorage.setItem(key, JSON.stringify(value));
        };

        this.getData = function(key) {
            if (localStorage.getItem(key) == null) {
                return false;
            } else {
                return JSON.parse(localStorage.getItem(key));
            }
        };

        this.deleteData = function(key) {
            localStorage.removeItem(key);
        };

        // user verification auth service
        this.isAuthenticated = function() {
            if (this.getData('userKey')) {
                return true;
            } else {
                return false;
            }
        };

        this.resetStorage = function() {
            localStorage.clear();
        };

        this.showLoader = function() {
            angular.element("#sim-loader").show();
            angular.element(".web-container").addClass('low-screen');
        };

        this.hideLoader = function() {
            angular.element("#sim-loader").fadeOut();
            angular.element(".web-container").removeClass('low-screen');
        };
    }

})();
