// define services here

// Basic utilities
    angular
        .module('evalai')
        .service('configService', configService);

    configService.$inject = ['EnvironmentConfig', 'BackendEndpoints'];

    function configService (EnvironmentConfig, BackendEndpoints) {
         return {
             "EnvironmentConfig": EnvironmentConfig,
             "BackendEndpoints": BackendEndpoints
         };

    }

