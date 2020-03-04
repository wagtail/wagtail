var gulp = require('gulp');
var gutil = require('gulp-util');
var path = require('path');
var config = require('../config');
var renameSrcToDest = require('../lib/rename-src-to-dest');

/*
 * Simple copy task - just copoes files from the source to the destination,
 * with no compilation, minification, or other intelligence.
 */
var simpleCopyTask = function(glob) {
    return function() {
        var sources = config.apps.map(function(app) {
            return path.join(app.sourceFiles, app.appName, glob);
        });

        return gulp.src(sources, {base: '.'})
            .pipe(renameSrcToDest())
            .pipe(gulp.dest('.'))
            .on('error', gutil.log);
    };
};

module.exports = simpleCopyTask;
