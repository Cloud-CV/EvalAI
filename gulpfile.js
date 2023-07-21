var gulp = require('gulp'),
    del = require('del'),
    _ = require('lodash'),
    fs = require('fs'),
    path = require('path'),
    concat = require('gulp-concat'),
    sass = require('gulp-sass'),
    postcss = require('gulp-postcss'),
    cleanCSS = require('gulp-clean-css'),
    sourcemaps = require('gulp-sourcemaps'),
    autoprefixer = require('autoprefixer'),
    merge = require('merge-stream'),
    rename = require('gulp-rename'),
    inject = require('gulp-inject'),
    uglify = require('gulp-uglify'),
    eslint = require('gulp-eslint'),
    cachebust = require('gulp-cache-bust'),
    connectModRewrite = require('connect-modrewrite'),
    connect = require('gulp-connect'),
    through = require('through2'),
    gulp_if = require('gulp-if'),
    replace = require('gulp-replace');

// development task
var production = false;
let timestamp;
var scripts = JSON.parse(fs.readFileSync('frontend/app.scripts.json'));
var styles = JSON.parse(fs.readFileSync('frontend/app.styles.json'));
var configJson = JSON.parse(fs.readFileSync('frontend/src/js/config.json'));

function clean() {
    return del(['frontend/dist/*']);
};

/*
Concat all js libs
*/
function vendorjs() {
    var paths = [];
    _.forIn(scripts.chunks, function(chunkScripts, chunkName) {
        chunkScripts.forEach(function(script) {
            var scriptFileName = scripts.paths[script];

            if (!fs.existsSync(__dirname + '/' + scriptFileName)) {

                throw console.error('Required path doesn\'t exist: ' + __dirname + '/' + scriptFileName, script)
            }
            paths.push(scriptFileName);
        });
    });
    return gulp.src(paths)
        .pipe(concat('vendor.js'))
        .pipe(gulp.dest("frontend/dist/vendors"))
}

/*
Concat all css libs
*/
function vendorcss() {
    var paths = [];
    _.forIn(styles.chunks, function(chunkStyles, chunkName) {
        chunkStyles.forEach(function(style) {
            var styleFileName = styles.paths[style];

            if (!fs.existsSync(__dirname + '/' + styleFileName)) {

                throw console.error('Required path doesn\'t exist: ' + __dirname + '/' + styleFileName, style)
            }
            paths.push(styleFileName);
        });
    });
    return gulp.src(paths)
        .pipe(concat('vendor.css'))
        .pipe(gulp.dest("frontend/dist/vendors"))
}

/*
minify and compress custom css files
*/
function css() {
    return gulp.src('frontend/src/css/main.scss')
        .pipe(sass().on('error', sass.logError))
        .pipe(sourcemaps.init())
        .pipe(postcss([autoprefixer()]))
        .pipe(gulp_if(production, cleanCSS()))
        .pipe(gulp_if(production, rename({ suffix: '.min' })))
        .pipe(sourcemaps.write())
        .pipe(gulp.dest('frontend/dist/css'))
        pipe(connect.reload());
}

/*
minify angular scripts
*/
function js() {
    var app = gulp.src('frontend/src/js/app.js')
        .pipe(concat('app.js'))
        .pipe(gulp_if(production, rename({ suffix: '.min' })))
        .pipe(gulp_if(production, uglify({ mangle: false })))
        .pipe(gulp.dest('frontend/dist/js'));

    var configs = gulp.src('frontend/src/js/route-config/*.js')
        .pipe(concat('route-config.js'))
        .pipe(gulp_if(production, rename({ suffix: '.min' })))
        .pipe(gulp_if(production, uglify({ mangle: false })))
        .pipe(gulp.dest('frontend/dist/js'));

    var controllers = gulp.src('frontend/src/js/controllers/*.js')
        .pipe(concat('controllers.js'))
        .pipe(gulp_if(production, rename({ suffix: '.min' })))
        .pipe(gulp_if(production, uglify({ mangle: false })))
        .pipe(gulp.dest('frontend/dist/js'));

    var directives = gulp.src('frontend/src/js/directives/*.js')
        .pipe(concat('directives.js'))
        .pipe(gulp_if(production, rename({ suffix: '.min' })))
        .pipe(gulp_if(production, uglify({ mangle: false })))
        .pipe(gulp.dest('frontend/dist/js'))

    var filters = gulp.src('frontend/src/js/filters/*.js')
        .pipe(concat('filters.js'))
        .pipe(gulp_if(production, rename({ suffix: '.min' })))
        .pipe(gulp_if(production, uglify({ mangle: false })))
        .pipe(gulp.dest('frontend/dist/js'));

    var services = gulp.src('frontend/src/js/services/*.js')
        .pipe(concat('services.js'))
        .pipe(gulp_if(production, rename({ suffix: '.min' })))
        .pipe(gulp_if(production, uglify({ mangle: false })))
        .pipe(gulp.dest('frontend/dist/js'))
    return merge(app, configs, controllers, directives, filters, services).
        pipe(connect.reload());
}

/*
minify and compress html files
*/
function html() {
    return gulp.src('frontend/src/views/web/**/*.html')
        // .pipe(gulp_if(production, htmlmin({ collapseWhitespace: true })))
        .pipe(gulp.dest('frontend/dist/views/web/'))
        .pipe(connect.reload());
}


/*
for image compression
*/
function images() {
    return gulp.src('frontend/src/images/**/*')
        // .pipe(gulp_if(production, imagemin()))
        .pipe(gulp.dest('frontend/dist/images'));
}

/*
Fonts
*/
function fonts() {
    var font = gulp.src([
            'bower_components/font-awesome/fonts/fontawesome-webfont.*',
            'bower_components/materialize/fonts/**/*',
            'frontend/src/fonts/*'
        ])
        .pipe(gulp.dest('frontend/dist/fonts/'));

    var fontCss = gulp.src([
            'bower_components/font-awesome/css/font-awesome.css'
        ])
        .pipe(gulp_if(production, cleanCSS()))
        .pipe(gulp_if(production, rename({ suffix: '.min' })))
        .pipe(sourcemaps.write())
        .pipe(gulp.dest('frontend/dist/css/'));

    return merge(font, fontCss);
}

/*
config for prod server
*/
function configProd() {
    return gulp.src('frontend/src/js/config.sample.js')
        .pipe(replace('moduleName', 'evalai-config'))
        .pipe(replace('constantName', Object.keys(configJson.production)))
        .pipe(replace('configKey', Object.keys(configJson.production.EnvironmentConfig)))
        .pipe(replace('configValue', configJson.production.EnvironmentConfig.API))
        .pipe(rename({
            basename: 'config'
        }))
        .pipe(gulp_if(production, rename({ suffix: '.min' })))
        .pipe(gulp.dest('frontend/dist/js'))
}

/* 
config for staging server
*/
function configStaging() {
    return gulp.src('frontend/src/js/config.sample.js')
        .pipe(replace('moduleName', 'evalai-config'))
        .pipe(replace('constantName', Object.keys(configJson.staging)))
        .pipe(replace('configKey', Object.keys(configJson.staging.EnvironmentConfig)))
        .pipe(replace('configValue', configJson.staging.EnvironmentConfig.API))
        .pipe(rename({
            basename: 'config'
        }))
        .pipe(gulp_if(production, rename({ suffix: '.min' })))
        .pipe(gulp.dest('frontend/dist/js/'))
}

/*
config for dev server
*/
function configDev() {
    return gulp.src('frontend/src/js/config.sample.js')
        .pipe(replace('moduleName', 'evalai-config'))
        .pipe(replace('constantName', Object.keys(configJson.local)))
        .pipe(replace('configKey', Object.keys(configJson.local.EnvironmentConfig)))
        .pipe(replace('configValue', configJson.local.EnvironmentConfig.API))
        .pipe(rename({
            basename: 'config'
        }))
        .pipe(gulp_if(production, rename({ suffix: '.min' })))
        .pipe(gulp.dest('frontend/dist/js/'))
}

/*
Inject path of css and js files in index.html 
*/
function injectpaths() {
    var target = gulp.src('frontend/base.html');
    var sources = gulp.src([
        'frontend/dist/vendors/*.js',
        'frontend/dist/js/*.js',
        'frontend/dist/vendors/*.css',
        'frontend/dist/css/*.css',
    ], { read: false });
    return target
        .pipe(inject(sources, { ignorePath: 'frontend', addRootSlash: true }))
        .pipe(gulp_if('*.js', production ? uglify() : gulp.dest('dist')))
        .pipe(gulp_if('*.css', production ? cleanCSS() : gulp.dest('dist')))
        .pipe(production ? cachebust({ type: 'timestamp' }) : gulp.dest('dist'))
        .pipe(through.obj((file, enc, cb) => {
            // Extract the timestamp value from the file contents
            const fileContents = file.contents.toString();
            const regex = /\?t=(\d+)/;
            const matches = fileContents.match(regex);
            if (matches && matches[1]) {
              timestamp = matches[1];
            }
            cb(null, file);
          }))
        .pipe(rename({
            basename: "index"
        }))
        .pipe(gulp.dest('frontend/'));
}

function replacetimestamp() {
    return gulp.src('frontend/dist/**/*.*')
    .pipe(replace('___REPLACE_IN_GULP___', timestamp))
    .pipe(gulp.dest('frontend/dist'));
}

/*
js linting
*/
var lint_path = {
    js: ['frontend/src/js/**/*.js', ]
}

function lint() {
    return gulp.src(lint_path.js)
        .pipe(eslint({}))
        .pipe(eslint.format())
        .pipe(eslint.results(function(results) {
            // Get the count of lint errors 
            var countError = results.errorCount;
            //Get the count of lint warnings
            var countWarning = results.warningCount;
            if (countError === 0) {
                if (countWarning > 0) {
                    console.warn("Please remove lint warnings in production env.");
                }
            } else {
                connect.serverClose();
                console.error("Please remove lint errors to connect the server");
            }
        }))
        .pipe(eslint.failAfterError())
}

/* 
Start a server for serving frontend
*/
function startServer() {
    // initially close the existance server if exists
    connect.serverClose();
    connect.server({
        root: 'frontend/',
        port: 8888,
        host: '0.0.0.0',
        livereload: true,
        middleware: function(connect) {
            return [
                connectModRewrite([
                    '!\\.html|\\.js|\\.css|\\.ico|\\.png|\\.gif|\\.jpg|\\.woff|.\\.ttf|.\\otf|\\.jpeg|\\.swf.*$ /index.html [NC,L]'
                ])
            ];
        }
    });
}

function watch() {
    gulp.watch('frontend/src/js/**/*.js', js);
    gulp.watch('frontend/src/css/**/*.scss', css);
    gulp.watch('frontend/src/views/web/**/*.html', html);
    gulp.watch('frontend/src/images/**/*', images);
    gulp.watch('bower_components/materialize/fonts/**/*', fonts);
    gulp.watch('bower_components/materialize/fonts/**/*', fonts);
}



var parallelTasks = gulp.parallel(vendorcss, vendorjs, css, js, html, images, fonts);

gulp.task('production', gulp.series(clean, function(done) {
    production = true;
    done();
}, parallelTasks, configProd, injectpaths, replacetimestamp, lint));

gulp.task('staging', gulp.series(clean, function(done) {
    production = true;
    done();
}, parallelTasks, configStaging, injectpaths, replacetimestamp, lint));

gulp.task('dev', gulp.series(clean, function(done) {
    production = false;
    done();
}, parallelTasks, configDev, injectpaths, lint));

gulp.task('dev:runserver', gulp.series(clean ,function(done) {
    production = false;
    done();
}, parallelTasks, configDev, injectpaths, lint, gulp.parallel(watch, startServer)));

gulp.task('runserver', gulp.series(function(done) {
    production = false;
    done();
}, gulp.parallel(watch, startServer)));
