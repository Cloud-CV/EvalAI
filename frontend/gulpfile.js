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
    connect = require('gulp-connect');
    htmlmin = require('gulp-html-minifier');
 


// minify and compress CSS files
gulp.task('css', function(){
     return sass('src/css/main.scss', { style: 'expanded' })
        .pipe(autoprefixer('last 2 version'))
        .pipe(gulp.dest('dist/assets/css'))
        .pipe(rename({suffix: '.min'}))
        .pipe(cssnano())
        .pipe(gulp.dest('dist/assets/css'));
})

// minify angular scripts
gulp.task('js', function() {
  var app = gulp.src('src/js/app.js')
            .pipe(jshint.reporter('default'))
            .pipe(concat('app.js'))
            .pipe(gulp.dest('dist/assets/js'))
            .pipe(rename({ suffix: '.min' }))
            .pipe(uglify())
            .pipe(gulp.dest('dist/assets/js'));

  var controllers = gulp.src('src/js/controllers/*.js')
                    .pipe(jshint.reporter('default'))
                    .pipe(concat('controllers.js'))
                    .pipe(gulp.dest('dist/assets/js'))
                    .pipe(rename({ suffix: '.min' }))
                    .pipe(uglify())
                    .pipe(gulp.dest('dist/assets/js'));

  var directives = gulp.src('src/js/directives/*.js')
                    .pipe(jshint.reporter('default'))
                    .pipe(concat('directives.js'))
                    .pipe(gulp.dest('dist/assets/js'))
                    .pipe(rename({ suffix: '.min' }))
                    .pipe(uglify())
                    .pipe(gulp.dest('dist/assets/js'));
  
  var services = gulp.src('src/js/services/*.js')
                    .pipe(jshint.reporter('default'))
                    .pipe(concat('services.js'))
                    .pipe(gulp.dest('dist/assets/js'))
                    .pipe(rename({ suffix: '.min' }))
                    .pipe(uglify())
                    .pipe(gulp.dest('dist/assets/js'));    

    return merge(app, controllers, directives, services)              
});

// minify and compress html files
gulp.task('html', function() {

  var landing_html = gulp.src('src/views/*.html')
    .pipe(htmlmin({collapseWhitespace: true }))
    .pipe(gulp.dest('dist/assets/views'));

    return merge(landing_html);
});


// for image compression
gulp.task('images', function() {
  return gulp.src('src/images/**/*')
    .pipe(imagemin({ optimizationLevel: 3, progressive: true, interlaced: true }))
    .pipe(gulp.dest('dist/assets/images'))
    .pipe(notify({ message: 'Images task complete' }));
});


// cleaning build process- run clean before deploy and rebuild files again
gulp.task('clean', function() {
    return del(['dist/assets/css', 'dist/assets/js', 'dist/assets/images',  'dist/assets/views']);
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
  gulp.watch(['dist/**']).on('change', livereload.changed);

});


// connect to server

gulp.task('connect', function(){
    connect.server({
      port: 8888
    });
})

// run by default
gulp.task('default', ['clean', 'connect'], function() {
    gulp.start('css', 'js', 'html', 'images');
});
