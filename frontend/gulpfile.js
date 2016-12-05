// Gulp Tasks
'use strict';

var gulp = require('gulp'),
    merge = require('merge-stream'),
    sass = require('gulp-ruby-sass'),
    autoprefixer = require('gulp-autoprefixer'),
    cssnano = require('gulp-cssnano'),
    jshint = require('gulp-jshint'),
    uglify = require('gulp-uglify'),
    imagemin = require('gulp-imagemin'),
    rename = require('gulp-rename'),
    concat = require('gulp-concat'),
    notify = require('gulp-notify'),
    cache = require('gulp-cache'),
    livereload = require('gulp-livereload'),
    del = require('del'),
    connect = require('gulp-connect'),
    htmlmin = require('gulp-html-minifier'),
    fs = require('fs'),
    connectModRewrite = require('connect-modrewrite'),
    ngConfig = require('gulp-ng-config'),
    prettyError = require('gulp-prettyerror'),
    // path = require('gulp-path'),
    // conf = require('./conf')(gulp),
    _ = require('lodash');


var scripts = require('./app.scripts.json');
var styles = require('./app.styles.json');


//include all bower scripts files
gulp.task('vendorjs', function() {

    _.forIn(scripts.chunks, function(chunkScripts, chunkName) {
        var paths = [];
        chunkScripts.forEach(function(script) {
            var scriptFileName = scripts.paths[script];

            if (!fs.existsSync(__dirname + '/' + scriptFileName)) {

                throw console.error('Required path doesn\'t exist: ' + __dirname + '/' + scriptFileName, script)
            }
            paths.push(scriptFileName);
        });
        gulp.src(paths)
            .pipe(concat(chunkName + '.js'))
            //.on('error', swallowError)
            .pipe(gulp.dest("./dist/vendors"))
    })

});


//include all bower  styles files
gulp.task('vendorcss', function() {

    _.forIn(styles.chunks, function(chunkStyles, chunkName) {
        var paths = [];
        chunkStyles.forEach(function(style) {
            var styleFileName = styles.paths[style];

            if (!fs.existsSync(__dirname + '/' + styleFileName)) {

                throw console.error('Required path doesn\'t exist: ' + __dirname + '/' + styleFileName, style)
            }
            paths.push(styleFileName);
        });
        gulp.src(paths)
            .pipe(concat(chunkName + '.css'))
            //.on('error', swallowError)
            .pipe(gulp.dest("./dist/vendors"))
    })

});

// config for dev server
gulp.task('configDev', function() {
    gulp.src('src/js/config.json')
        .pipe(ngConfig('evalai-config', {
            environment: 'local'
        }))
        .pipe(gulp.dest('./dist/js'))
});

// config for prod server
gulp.task('configProd', function() {
    gulp.src('src/js/config.json')
        .pipe(ngConfig('evalai-config', {
            environment: 'production'
        }))
        .pipe(gulp.dest('./dist/js'))
});

// minify and compress CSS files
gulp.task('css', function() {
    return sass('src/css/main.scss', { style: 'expanded' })
        .pipe(prettyError())
        .pipe(autoprefixer('last 2 version'))
        .pipe(gulp.dest('./dist/css'))
        .pipe(rename({ suffix: '.min' }))
        .pipe(cssnano())
        .pipe(gulp.dest('./dist/css'));
})

// minify angular scripts
gulp.task('js', function() {

    var app = gulp.src('src/js/app.js')
        .pipe(prettyError())
        .pipe(jshint.reporter('default'))
        .pipe(concat('app.js'))
        .pipe(gulp.dest('./dist/js'))
        .pipe(rename({ suffix: '.min' }))
        .pipe(uglify())
        .pipe(gulp.dest('./dist/js'));

    var configs = gulp.src('src/js/route-config/*.js')
        .pipe(prettyError())
        .pipe(jshint.reporter('default'))
        .pipe(concat('route-config.js'))
        .pipe(gulp.dest('./dist/js'))
        .pipe(rename({ suffix: '.min' }))
        .pipe(uglify())
        .pipe(gulp.dest('./dist/js'));

    var controllers = gulp.src('src/js/controllers/*.js')
        .pipe(prettyError())
        .pipe(jshint.reporter('default'))
        .pipe(concat('controllers.js'))
        .pipe(gulp.dest('./dist/js'))
        .pipe(rename({ suffix: '.min' }))
        .pipe(uglify())
        .pipe(gulp.dest('./dist/js'));

    var directives = gulp.src('src/js/directives/*.js')
        .pipe(prettyError())
        .pipe(jshint.reporter('default'))
        .pipe(concat('directives.js'))
        .pipe(gulp.dest('./dist/js'))
        .pipe(rename({ suffix: '.min' }))
        .pipe(uglify())
        .pipe(gulp.dest('./dist/js'));

    var filters = gulp.src('src/js/filters/*.js')
        .pipe(prettyError())
        .pipe(jshint.reporter('default'))
        .pipe(concat('filters.js'))
        .pipe(gulp.dest('./dist/js'))
        .pipe(rename({ suffix: '.min' }))
        .pipe(uglify())
        .pipe(gulp.dest('./dist/js'));

    var services = gulp.src('src/js/services/*.js')
        .pipe(prettyError())
        .pipe(jshint.reporter('default'))
        .pipe(concat('services.js'))
        .pipe(gulp.dest('./dist/js'))
        .pipe(rename({ suffix: '.min' }))
        .pipe(uglify())
        .pipe(gulp.dest('./dist/js'));

    return merge(app, configs, controllers, directives, filters, services)
});


// minify and compress html files
gulp.task('html', function() {

    var webViews = gulp.src('src/views/web/*.html')
        .pipe(htmlmin({ collapseWhitespace: true }))
        .pipe(gulp.dest('./dist/views/web'));

    var webPartials = gulp.src('src/views/web/partials/*.html')
        .pipe(htmlmin({ collapseWhitespace: true }))
        .pipe(gulp.dest('./dist/views/web/partials'));

    return merge(webViews, webPartials);
});


// for image compression
gulp.task('images', function() {
    return gulp.src('src/images/**/*')
        .pipe(imagemin({ optimizationLevel: 3, progressive: true, interlaced: true }))
        .pipe(gulp.dest('./dist/images'));
});


// Fonts
gulp.task('fonts', function() {
    var font = gulp.src([
            'bower_components/font-awesome/fonts/fontawesome-webfont.*', 'bower_components/materialize/fonts/**/*'
        ])
        .pipe(gulp.dest('dist/fonts/'));

    var fontCss = gulp.src([
            'bower_components/font-awesome/css/font-awesome.css'
        ])
        .pipe(gulp.dest('dist/css/'));

    return merge(font, fontCss);
});


// cleaning build process- run clean before deploy and rebuild files again
gulp.task('clean', function() {
    return del(['./dist/css', './dist/js', './dist/images', '../dist/vendors', './dist/views'], { force: true });
});


// watch function
gulp.task('watch', function() {

    // Watch .scss files
    gulp.watch('src/css/**/*.scss', ['css']);

    // Watch .js files
    gulp.watch('src/js/**/*.js', ['js']);

    // Watch html files
    gulp.watch('src/views/**/*.html', ['html']);

    // Watch image files
    gulp.watch('src/images/**/*', ['images']);

    // Create LiveReload server
    livereload.listen();

    // Watch any files in dist/, reload on change
    gulp.watch(['./dist/**']).on('change', livereload.changed);

});


// connect to server
gulp.task('connect', function() {
    connect.server({
        root: './',
        port: 8888,
        middleware: function(connect) {
            return [
                connectModRewrite([
                    '!\\.html|\\.js|\\.css|\\.ico|\\.png|\\.gif|\\.jpg|\\.woff|.\\.ttf|.\\otf|\\.jpeg|\\.swf.*$ /index.html [NC,L]'
                ])
            ];
        }
    });
})

// development task
gulp.task('dev', ['clean'], function() {
    gulp.start('css', 'js', 'html', 'images', 'vendorjs', 'vendorcss', 'fonts', 'configDev');
});

// production task
gulp.task('prod', ['clean'], function() {
    gulp.start('css', 'js', 'html', 'images', 'vendorjs', 'vendorcss', 'fonts', 'configProd');
});
