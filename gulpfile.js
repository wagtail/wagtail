var gulp = require('gulp');
var gutil = require('gulp-util');
var rename = require('gulp-rename');
var path = require('path');


gulp.task('default', ['build', 'watch']);
gulp.task('build', ['styles', 'javascript', 'images', 'fonts']);


var sourceDirName = 'static_src';
var destDirName = 'static';
var renameSrcToDest = function() {
	return rename(function(filePath) {
		filePath.dirname = filePath.dirname.replace(
			'/' + sourceDirName + '/',
			'/' + destDirName + '/');
	});
};

var flatten = function(arrOfArr) {
	return arrOfArr.reduce(function(flat, more) {
		return flat.concat(more);
	}, []);
};


// A Wagtail app that contains static files
var App = function(dir, options) {
	this.dir = dir;
	this.options = options || {};
	this.appName = this.options.appName || path.basename(dir);
	this.sourceFiles = path.join('.', this.dir, sourceDirName);
};
App.prototype = Object.create(null);
App.prototype.scssIncludePaths = function() {
	return [this.sourceFiles];
};
App.prototype.scssSources = function() {
	if (!this.options.scss) return [];

	return this.options.scss.map(function(file) {
		return path.join(this.sourceFiles, file);
	}, this);
};


// All the Wagtail apps that contain static files
var apps = [
	new App('wagtail/wagtailadmin', {
		'scss': [
			'wagtailadmin/scss/core.scss',
			'wagtailadmin/scss/layouts/login.scss',
			'wagtailadmin/scss/layouts/home.scss',
			'wagtailadmin/scss/layouts/page-editor.scss',
			'wagtailadmin/scss/layouts/preview.scss',
			'wagtailadmin/scss/panels/rich-text.scss',
			'wagtailadmin/scss/userbar.scss',
			'wagtailadmin/scss/userbar_embed.scss',
		],
	}),
	new App('wagtail/wagtaildocs'),
	new App('wagtail/wagtailembeds'),
	new App('wagtail/wagtailforms'),
	new App('wagtail/wagtailimages', {
		'scss': [
			'wagtailimages/scss/add-multiple.scss',
			'wagtailimages/scss/focal-point-chooser.scss',
		],
	}),
	new App('wagtail/wagtailsnippets'),
	new App('wagtail/wagtailusers', {
		'scss': [
			'wagtailusers/scss/groups_edit.scss',
		],
	}),
	new App('wagtail/contrib/wagtailstyleguide', {
		'scss': [
			'wagtailstyleguide/scss/styleguide.scss'
		],
	}),
];


/*
 * Watch - Watch files, trigger tasks when they are modified
 */
gulp.task('watch', ['build'], function () {
	apps.forEach(function(app) {
		gulp.watch(path.join(app.sourceFiles, '*/scss/**'), ['styles:sass']);
		gulp.watch(path.join(app.sourceFiles, '*/css/**'), ['styles:css']);
		gulp.watch(path.join(app.sourceFiles, '*/js/**'), ['javascript']);
		gulp.watch(path.join(app.sourceFiles, '*/images/**'), ['images']);
		gulp.watch(path.join(app.sourceFiles, '*/fonts/**'), ['fonts']);
	});
});


/*
 * Styles
**/
gulp.task('styles', ['styles:sass', 'styles:css']);

// SASS - Compile and move sass
gulp.task('styles:sass', function () {
	var sass = require('gulp-sass');
	var autoprefixer = require('gulp-autoprefixer');

	// Wagtail Sass files include each other across applications,
	// e.g. wagtailimages Sass files will include wagtailadmin/sass/mixins.scss
	// Thus, each app is used as an includePath.
	var includePaths = flatten(apps.map(function(app) { return app.scssIncludePaths() }))

	// Not all files in a directory need to be compiled, so each app defines
	// its own Sass files that need to be compiled.
	var sources = flatten(apps.map(function(app) { return app.scssSources(); }));

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
			return file.base
				.replace('/static_src/', '/static/')
				.replace('/scss/', '/css/');
		}))
		.on('error', gutil.log);
});


/*
 * Simple copy tasks - these just copy files from the source to the destination,
 * with no compilation, minification, or other intelligence
 *
**/
var rename = require('gulp-rename');
var simpleCopyTask = function(glob) {
	return function() {
		var sources = apps.map(function(app) {
			return path.join(app.sourceFiles, app.appName, glob);
		});

		return gulp.src(sources, {base: '.'})
			.pipe(renameSrcToDest())
			.pipe(gulp.dest('.'))
			.on('error', gutil.log);
	};
};
gulp.task('styles:css', simpleCopyTask('css/**/*'));
gulp.task('javascript', simpleCopyTask('js/**/*'));
gulp.task('images', simpleCopyTask('images/**/*'));
gulp.task('fonts', simpleCopyTask('fonts/**/*'));
