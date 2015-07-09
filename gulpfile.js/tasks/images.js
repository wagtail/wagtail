var gulp = require('gulp');
var simpleCopyTask = require('../lib/simplyCopy');

gulp.task('images', simpleCopyTask('images/**/*'));
