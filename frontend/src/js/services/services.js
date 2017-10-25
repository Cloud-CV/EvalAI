// define services here

// Basic utilities
(function() {

    'use strict';

    angular
        .module('evalai')
        .service('utilities', utilities);

    utilities.$inject = ['$http', 'EnvironmentConfig', '$rootScope'];

    function utilities($http, EnvironmentConfig) {

        // factory for API calls
        this.sendRequest = function(parameters, header, type) {
            var url = EnvironmentConfig.API + parameters.url;
            var data = parameters.data;
            var token = parameters.token;
            var method = parameters.method;
            var successCallback = parameters.callback.onSuccess;
            var errorCallback = parameters.callback.onError;

            // check for authenticated calls
            if (parameters.token != null) {
                var headers = {
                    'Authorization': "Token " + token
                };
            }

            // function to check for applying header
            function pick(arg, def) {
                return (typeof arg == 'undefined' ? def : arg);
            }

            header = pick(header, 'header');
            var req = {
                method: method,
                url: url,
            };
            if (header == 'header') {
                req.headers = headers;
            }
            if (method == "POST" || method == "PUT" || method == "PATCH") {
                req.data = data;
            }

            // for file upload
            if (method == "POST" || method == "PATCH" || method == "PUT") {
                if (type == "upload") {
                    // alert("")
                    headers = {
                        'Content-Type': undefined,
                        'Authorization': "Token " + token
                    };
                    req.transformRequest = function(data) {
                        return data;
                    };

                    req.headers = headers;
                }
            }

            $http(req)
                .then(successCallback, errorCallback);
        };

        this.storeData = function(key, value) {
            localStorage.setItem(key, JSON.stringify(value));
        };

        this.getData = function(key) {
            if (localStorage.getItem(key) === null) {
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
