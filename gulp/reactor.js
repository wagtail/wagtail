var gulp        = require('gulp');
var gutil       = require("gulp-util");
var source      = require('vinyl-source-stream');
var browserify  = require('browserify');
var watchify    = require('watchify');
var reactify    = require("reactify");
var livereload  = require("gulp-livereload");
var rename      = require("gulp-rename");
var jshint      = require('gulp-jshint');
var path        = require("path");
var uglify      = require("gulp-uglify");
var streamify   = require("gulp-streamify");
var glob        = require("glob");




var babelify = require("babelify");

// Main JS entrypoint config
var jsPath          = path.join( __dirname, "..",  "wagtail", "wagtailadmin", "static", "wagtailadmin", "js");
var jsEntryPoint    = path.join( __dirname, "..",  "wagtail", "wagtailadmin", "static-src", "js", "explorer.js");
var jsBundleDest    = jsPath;
var jsBundleName    = "explorer-menu.js";

// Only need initial file, browserify finds the deps
// We want to convert JSX to normal javascript
// Gives us sourcemapping
// Requirement of watchify
function getBundler(debug) {
    return browserify({
        entries: [jsEntryPoint],
        // transform: [babelify],
        debug: debug,
        cache: {}, packageCache: {}, fullPaths: debug
    }).transform(babelify)
}

function handleError(err) {
    gutil.log(err.message);
    // this.end();
}


/**
 * Bundle browserify entry points
 * @param  {Function} done  Callback executed when all bundles complete
 * @return {[type]}         undefined
 */
gulp.task('bundle', function() {
    var bundler = getBundler(true);
    var watcher  = watchify(bundler);

    function rebundle (file) {
        var updateStart = Date.now(), elapsed;
        gutil.log('Bundle start');

        if (file) {
           gutil.log(file);
        }

        watcher.bundle()
            .on('error', handleError)
            .pipe(source(jsBundleName))
            .pipe(gutil.env.type === 'production' ? uglify() : gutil.noop() )
            .pipe(gulp.dest(jsBundleDest))
            .pipe(livereload());

        elapsed = Date.now() - updateStart;

        gutil.log('Bundled', elapsed + 'ms');
    }

    return watcher
        .on('update', rebundle)
        // Create the initial bundle when starting the task
        .bundle()
        .on('error', handleError)
        .pipe(gutil.env.type === 'production' ? uglify() : gutil.noop() )
        .pipe(source(jsBundleName))
        .pipe(gulp.dest(jsBundleDest));
});

gulp.task("lint:js", function() {
    return gulp.src(path.join(__dirname, "..", "wagtail", "wagtailadmin", "static-src", "js", "**", "*.js" ))
        .pipe(jshint())
        .pipe(jshint.reporter('default'))
});
