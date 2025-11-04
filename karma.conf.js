// Set CHROME_BIN based on availability
const isArm = require('os').arch().includes('arm');

// Use system Chrome/Chromium paths (Docker container has Chrome installed)
process.env.CHROME_BIN = process.env.CHROME_BIN || (isArm ? '/usr/bin/chromium' : '/usr/bin/google-chrome');
module.exports = function(config) {
    var configuration = {
  
      // base path that will be used to resolve all patterns (eg. files, exclude)
      basePath: '',
  
      // frameworks to use
      // available frameworks: https://npmjs.org/browse/keyword/karma-adapter
      frameworks: ['jasmine'],

    customLaunchers: {
        ChromiumHeadlessNoSandbox: {
          base: 'ChromiumHeadless',
          flags: [
            '--no-sandbox', 
            '--disable-gpu', 
            '--disable-dev-shm-usage',
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor'
          ]
        },
        ChromeWithNoSandbox: {
          base: 'ChromeHeadless',
          flags: [
            '--no-sandbox',
            '--disable-gpu',
            '--disable-dev-shm-usage',
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor',
            '--disable-software-rasterizer',
            '--disable-extensions',
            '--remote-debugging-port=9222'
          ],
        },
      },
  
      browsers: [isArm ? 'ChromiumHeadlessNoSandbox' : 'ChromeWithNoSandbox'],  
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
        'karma-brief-reporter',
        'karma-junit-reporter',
    ],

    // test results reporter to use
    // possible values: 'dots', 'progress'
    // available reporters: https://npmjs.org/browse/keyword/karma-reporter
    reporters: ['coverage', 'brief', 'junit'],

    // JUnit reporter configuration
    junitReporter: {
        outputDir: 'coverage/frontend/',
        outputFile: 'TEST-frontend.xml',
        suite: 'frontend'
    },


    // web server port
    port: 9876,


    // enable / disable colors in the output (reporters and logs)
    colors: true,


    // level of logging
    // possible values: config.LOG_DISABLE || config.LOG_ERROR || config.LOG_WARN || config.LOG_INFO || config.LOG_DEBUG
    logLevel: config.LOG_INFO,


    // enable / disable watching file and executing tests whenever any file changes
    autoWatch: false,


    // Continuous Integration mode
    // if true, Karma captures browsers, runs the tests and exits
    singleRun: true,

    // Concurrency level
    // how many browser should be started simultaneous
    concurrency: 1,

    // Browser disconnect timeout
    browserDisconnectTimeout: 10000,
    browserDisconnectTolerance: 3,
    browserNoActivityTimeout: 60000,
    
    // Force process exit after tests complete
    processKillTimeout: 2000,
    captureTimeout: 60000,

    coverageReporter: {
        includeAllSources: true,
        dir: 'coverage/frontend/',
        reporters: [
            { type: 'lcovonly', subdir: '.', file: 'lcov.info' },
            { type: 'text-summary' }
        ]
    }
  };

  // Detect if this is TravisCI running the tests and tell it to use chromium
  if(process.env.TRAVIS){
      configuration.browsers = ['ChromeWithNoSandbox'];
      configuration.browserDisconnectTimeout = 20000;
      configuration.browserDisconnectTolerance = 5;
      configuration.browserNoActivityTimeout = 120000;
  }

  config.set(configuration);
}
