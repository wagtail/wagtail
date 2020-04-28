var gulp = require('gulp');

gulp.task('build', gulp.series('styles', 'scripts', 'images', 'fonts'));
