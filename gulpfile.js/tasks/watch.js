var gulp = require('gulp');
var path = require('path');
var config = require('../config');


const paths = config.apps.reduce((_, app) => ({
    'styles:sass': [...(_['styles:sass'] || []), path.join('./client/**/*.scss'), path.join(app.sourceFiles, '*/scss/**')],
    'styles:css': [...(_['styles:css'] || []), path.join(app.sourceFiles, '*/css/**')],
    'scripts': [...(_['scripts'] || []), path.join(app.sourceFiles, '*/js/**')],
    'images': [...(_['images'] || []), path.join(app.sourceFiles, '*/images/**')],
    'fonts': [...(_['fonts'] || []), path.join(app.sourceFiles, '*/fonts/**')],
}), {});

/*
 * Watch - Watch files, trigger tasks when they are modified
 */
gulp.task('watch', gulp.series('build', function (cb) {
    gulp.watch(paths['styles:sass'], gulp.series('styles:sass'));
    gulp.watch(paths['styles:css'], gulp.series('styles:css'));
    gulp.watch(paths['scripts'], gulp.series('scripts'));
    gulp.watch(paths['images' ], gulp.series('images' ));
    gulp.watch(paths['fonts' ], gulp.series('fonts' ));    
}));
