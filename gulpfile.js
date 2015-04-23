var gulp = require('gulp');
var gutil = require('gulp-util');
var rename = require('gulp-rename');
var path = require('path');
var join = path.join;


gulp.task('default', ['watch']);
gulp.task('build', ['styles']);

var scssFiles = {
	'wagtail/wagtailadmin/static': [
		'wagtailadmin/scss/core.scss',
		'wagtailadmin/scss/layouts/login.scss',
		'wagtailadmin/scss/layouts/home.scss',
		'wagtailadmin/scss/layouts/page-editor.scss',
		'wagtailadmin/scss/layouts/preview.scss',
		'wagtailadmin/scss/panels/rich-text.scss',
		'wagtailadmin/scss/userbar.scss',
		'wagtailadmin/scss/normalize.scss',
		'wagtailadmin/scss/userbar_embed.scss',
	],
	'wagtail/wagtailimages/static': [
		'wagtailimages/scss/add-multiple.scss',
		'wagtailimages/scss/focal-point-chooser.scss',
	],
	'wagtail/wagtailusers/static': [
		'wagtailusers/scss/groups_edit.scss',
	],
	'wagtail/contrib/wagtailstyleguide/static': [
		'wagtailstyleguide/scss/styleguide.scss',
	],
};


/*
 * Watch - Watch files, trigger tasks when they are modified
 */
gulp.task('watch', ['build'], function () {
	for (var appPath in scssFiles) {
		gulp.watch(join(appPath, '*/scss/**'), ['styles']);
	}
});


/*
 * SASS - Compile and move sass
**/

gulp.task('styles', function () {
	var sass = require('gulp-sass');
	var autoprefixer = require('gulp-autoprefixer');

	// Wagtail Sass files include each other across applications,
	// e.g. wagtailimages Sass files will include wagtailadmin/scss/mixins.scss
	// Thus, each app is used as an includePath.
	var includePaths = Object.keys(scssFiles);

	// Not all files in a directory need to be compiled, so globs can not be used.
	// Each file is named individually by joining its app path and file name.
	var sources = Object.keys(scssFiles).reduce(function(allSources, appPath) {
		var appSources = scssFiles[appPath];
		return allSources.concat(appSources.map(function(appSource) {
			return join(appPath, appSource);
		}));
	}, []);

	return gulp.src(sources)
		.pipe(sass({
			errLogToConsole: true,
			includePaths: includePaths,
			outputStyle: 'expanded'
		}))
		.pipe(autoprefixer({
			browsers: ['last 2 versions'],
			cascade: false
		}))
		.pipe(gulp.dest(function(file) {
			// e.g. wagtailadmin/scss/core.scss -> wagtailadmin/css/core.css
			// Changing the suffix is done by Sass automatically
			return file.base.replace('/scss/', '/css/');
		}))
		.on('error', gutil.log);
});
