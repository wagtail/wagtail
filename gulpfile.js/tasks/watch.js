var gulp = require('gulp');
var path = require('path');
var config = require('../config');

/*
 * Watch - Watch files, trigger tasks when they are modified
 */
gulp.task('watch', ['build'], function () {
    config.apps.forEach(function(app) {
        gulp.watch(path.join('./client/src/**/*.scss'), ['styles:sass']);
        gulp.watch(path.join(app.sourceFiles, '*/scss/**'), ['styles:sass']);
        gulp.watch(path.join(app.sourceFiles, '*/css/**'), ['styles:css']);
        gulp.watch(path.join(app.sourceFiles, '*/js/**'), ['scripts']);
        gulp.watch(path.join(app.sourceFiles, '*/images/**'), ['images']);
        gulp.watch(path.join(app.sourceFiles, '*/fonts/**'), ['fonts']);
    });
});
