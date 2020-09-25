var path = require('path');
var gulp = require('gulp');
var sass = require('gulp-dart-sass');
var postcss = require('gulp-postcss');
var autoprefixer = require('autoprefixer');
var cssnano = require('cssnano');
var postcssCustomProperties = require('postcss-custom-properties');
var postcssCalc = require('postcss-calc');
var sourcemaps = require('gulp-sourcemaps');
var size = require('gulp-size');
var config = require('../config');
var simpleCopyTask = require('../lib/simplyCopy');
var normalizePath = require('../lib/normalize-path');
var renameSrcToDest = require('../lib/rename-src-to-dest');
var gutil = require('gulp-util');

var flatten = function(arrOfArr) {
    return arrOfArr.reduce(function(flat, more) {
        return flat.concat(more);
    }, []);
};

var autoprefixerConfig = {
    cascade: false,
};

var cssnanoConfig = {
    discardUnused: {
        fontFace: false,
    },
    zindex: false,
};

// Copy all assets that are not CSS files.
gulp.task('styles:assets', simpleCopyTask('css/**/!(*.css)'));

gulp.task('styles:css', function() {
    var sources = config.apps.map(function(app) {
        return path.join(app.sourceFiles, app.appName, 'css/**/*.css');
    });

    return gulp.src(sources, {base: '.'})
        .pipe(postcss([
          cssnano(cssnanoConfig),
          autoprefixer(autoprefixerConfig),
        ]))
        .pipe(renameSrcToDest())
        .pipe(size({ title: 'Vendor CSS' }))
        .pipe(gulp.dest('.'))
        .on('error', gutil.log);
});

// For Sass files,
gulp.task('styles:sass', function () {
    // Wagtail Sass files include each other across applications,
    // e.g. wagtailimages Sass files will include wagtailadmin/sass/mixins.scss
    // Thus, each app is used as an includePath.
    var includePaths = flatten(config.apps.map(function(app) { return app.scssIncludePaths(); }));

    // Not all files in a directory need to be compiled, so each app defines
    // its own Sass files that need to be compiled.
    var sources = flatten(config.apps.map(function(app) { return app.scssSources(); }));

    return gulp.src(sources)
        .pipe(config.isProduction ? gutil.noop() : sourcemaps.init())
        .pipe(sass({
            errLogToConsole: true,
            includePaths: includePaths,
            outputStyle: 'expanded'
        }).on('error', sass.logError))
        .pipe(postcss([
          cssnano(cssnanoConfig),
          autoprefixer(autoprefixerConfig),
          postcssCustomProperties(),
          postcssCalc(),
        ]))
        .pipe(size({ title: 'Wagtail CSS' }))
        .pipe(config.isProduction ? gutil.noop() : sourcemaps.write())
        .pipe(gulp.dest(function (file) {
            // e.g. wagtailadmin/scss/core.scss -> wagtailadmin/css/core.css
            // Changing the suffix is done by Sass automatically
            return normalizePath(file.base)
                .replace(
                    '/' + config.srcDir + '/',
                    '/' + config.destDir + '/'
                )
                .replace('/scss', '/css');
        }))
        .on('error', gutil.log);
});

gulp.task('styles', gulp.series('styles:sass', 'styles:css', 'styles:assets'));
