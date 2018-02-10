// Karma configuration
// Generated on Tue Mar 14 2017 06:19:19 GMT+0530 (IST)

module.exports = function(config) {
    config.set({

        // base path that will be used to resolve all patterns (eg. files, exclude)
        basePath: '',


        // frameworks to use
        frameworks: ['mocha', 'chai'],


        // list of files / patterns to load in the browser
        files: [
            'frontend/dist/vendors/*.js',
            'frontend/dist/js/config.js',
            'node_modules/angular-mocks/angular-mocks.js',
            'frontend/src/js/app.js',
            'frontend/src/**/*.js',
            'frontend/tests/**/*.test.js'
        ],


        // list of files to exclude
        exclude: [],


        // preprocess matching files before serving them to the browser
        preprocessors: {},


        // test results reporter to use
        reporters: ['mocha'],


        // web server port
        port: 9876,


        // enable / disable colors in the output (reporters and logs)
        colors: true,


        // level of logging
        logLevel: config.LOG_INFO,


        // enable / disable watching file and executing tests whenever any file changes
        autoWatch: true,


        // start these browsers
        browsers: ['PhantomJS'],

        client: {
            captureConsole: true,
        },


        // Continuous Integration mode
        // if true, Karma captures browsers, runs the tests and exits
        // singleRun: true,

        // Concurrency level
        // how many browser should be started simultaneous
        concurrency: Infinity
    })
}
