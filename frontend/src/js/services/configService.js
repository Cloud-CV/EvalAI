// define services here

// Basic utilities
    angular
        .module('evalai')
        .service('configService', configService);

    configService.$inject = ['EnvironmentConfig'];

    function configService (EnvironmentConfig) {
         return EnvironmentConfig;

    }

