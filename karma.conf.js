const puppeteer = require('puppeteer');
process.env.CHROME_BIN = puppeteer.executablePath();

// Karma configuration
// Generated on Thu Apr 18 2019 11:48:30 GMT+0530 (India Standard Time)

module.exports = function(config) {
  var configuration = {

    // base path that will be used to resolve all patterns (eg. files, exclude)
    basePath: '',


    // frameworks to use
    // available frameworks: https://npmjs.org/browse/keyword/karma-adapter
    frameworks: ['jasmine'],

    customLaunchers: {
        ChromeWithNoSandbox: {
            base: 'ChromeHeadless',
            flags: ['--no-sandbox'],
        },
    },
    browsers: ['ChromeWithNoSandbox'],

    // list of files / patterns to load in the browser
    files: [
        'frontend/dist/vendors/*.js',
        'frontend/dist/js/config.js',
        'node_modules/angular-mocks/angular-mocks.js',
        'frontend/src/js/app.js',
        'frontend/src/**/*.js',
        'frontend/tests/**/*.test.js'
    ],


    // list of files / patterns to exclude
    exclude: [
    ],


    // preprocess matching files before serving them to the browser
    // available preprocessors: https://npmjs.org/browse/keyword/karma-preprocessor
    preprocessors: {
        'frontend/src/js/controllers/*.js': ['coverage']
    },

    plugins: [
        'karma-jasmine',
        'karma-chrome-launcher',
        'karma-coverage',
        'karma-coveralls',
        'karma-brief-reporter',
    ],

    // test results reporter to use
    // possible values: 'dots', 'progress'
    // available reporters: https://npmjs.org/browse/keyword/karma-reporter
    reporters: ['coverage', 'brief'],


    // web server port
    port: 9876,


    // enable / disable colors in the output (reporters and logs)
    colors: true,


    // level of logging
    // possible values: config.LOG_DISABLE || config.LOG_ERROR || config.LOG_WARN || config.LOG_INFO || config.LOG_DEBUG
    logLevel: config.LOG_INFO,


    // enable / disable watching file and executing tests whenever any file changes
    autoWatch: true,


    // Continuous Integration mode
    // if true, Karma captures browsers, runs the tests and exits
    singleRun: false,

    // Concurrency level
    // how many browser should be started simultaneous
    concurrency: Infinity,

    coverageReporter: {
        includeAllSources: true,
        dir: 'coverage/',
        reporters: [
            { type: "lcov" },
            { type: 'text-summary' }
        ]
    }
  };

  // Detect if this is TravisCI running the tests and tell it to use chromium
  if(process.env.TRAVIS){
      configuration.browsers = ['ChromeWithNoSandbox'];
  }

  config.set(configuration);
}
