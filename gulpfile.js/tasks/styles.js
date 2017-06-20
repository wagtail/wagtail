var gulp = require('gulp');
var sass = require('gulp-sass');
var config = require('../config');
var autoprefixer = require('gulp-autoprefixer');
var simpleCopyTask = require('../lib/simplyCopy');
var normalizePath = require('../lib/normalize-path');
var gutil = require('gulp-util');

var flatten = function(arrOfArr) {
    return arrOfArr.reduce(function(flat, more) {
        return flat.concat(more);
    }, []);
};

gulp.task('styles', ['styles:sass', 'styles:css']);

gulp.task('styles:css', simpleCopyTask('css/**/*'));

gulp.task('styles:sass', function () {
    // Wagtail Sass files include each other across applications,
    // e.g. wagtailimages Sass files will include wagtailadmin/sass/mixins.scss
    // Thus, each app is used as an includePath.
    var includePaths = flatten(config.apps.map(function(app) { return app.scssIncludePaths(); }));

    // Not all files in a directory need to be compiled, so each app defines
    // its own Sass files that need to be compiled.
    var sources = flatten(config.apps.map(function(app) { return app.scssSources(); }));

    return gulp.src(sources)
        .pipe(sass({
            errLogToConsole: true,
            includePaths: includePaths,
            outputStyle: 'expanded'
        }).on('error', sass.logError))
        .pipe(autoprefixer({
            browsers: ['last 3 versions', 'ie 11'],
            cascade: false
        }))
        .pipe(gulp.dest(function(file) {
            // e.g. wagtailadmin/scss/core.scss -> wagtailadmin/css/core.css
            // Changing the suffix is done by Sass automatically
            return normalizePath(file.base)
                .replace(
                    '/' + config.srcDir + '/',
                    '/' + config.destDir + '/'
                )
                .replace('/scss/', '/css/');
        }))
        .on('error', gutil.log);
});
