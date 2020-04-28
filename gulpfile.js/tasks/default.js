var gulp = require('gulp');

gulp.task('default', gulp.series('build', 'watch'));
