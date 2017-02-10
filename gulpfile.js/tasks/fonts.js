var gulp = require('gulp');
var simpleCopyTask = require('../lib/simplyCopy');

gulp.task('fonts', simpleCopyTask('fonts/**/*'));
