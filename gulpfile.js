var gulp = require("gulp");
var spawn = require("child_process").spawn;
// var sass = require("gulp-sass");
// var shell = require("gulp-shell");
var fs = require("fs");
var path = require("path");
// var grunt = require('gulp-grunt')(gulp);
// var pleeease = require('gulp-pleeease');
// var livereload = require('gulp-livereload');

/*
    ---------------------------------------------------------------------------
    Config
    ---------------------------------------------------------------------------

*/

var pkg = JSON.parse(fs.readFileSync("package.json"));

var webroot = "site/www";

var paths = {
    sass: path.join(webroot, "sass"),
    css: path.join(webroot, "css"),
    js: path.join(webroot, "includes")
};

/*
    ---------------------------------------------------------------------------
    Stylesheets
    ---------------------------------------------------------------------------
*/

// gulp.task('css', function () {

//     // set minifier to false to keep Sass sourcemaps support
//     var PleeeaseOptions = {
//         minifier: false,
//         autoprefixer: {
//             browsers: ['> 0.5%', 'last 3 versions', 'Firefox ESR', 'Opera 12.1']
//         },
//         sourcemaps: false,
//         mqpacker: true,
//         filters: false,
//         rem: true,
//         pseudoElements: false,
//         opacity: false
//     };

//     gulp.src(path.join(paths.sass, "**", "*.scss"))
//         .pipe(sass({ errLogToConsole: true }))
//         .pipe(pleeease(PleeeaseOptions))
//         .pipe(gulp.dest( paths.css ))
//         .pipe(livereload())
//     ;

// });



/*
 ---------------------------------------------------------------------------
 Icons
 ---------------------------------------------------------------------------
 */

// gulp.task('icon', function() {

//     gulp.run('grunt-icon');

// });

/*
    ---------------------------------------------------------------------------
    Hygine stuff
    ---------------------------------------------------------------------------
*/

// gulp.task('clean', function() {
//     del([
//         paths.build
//     ]);
// });


/*
 ---------------------------------------------------------------------------
 Wrangler
 ---------------------------------------------------------------------------
 */

// gulp.task('content', shell.task([
//     "wrangler build " + paths.content + " " + paths.webroot + " --force"
// ]));



require("./gulp/reactor");




/*
    ---------------------------------------------------------------------------
    Watching, touching, feeling, loving
    ---------------------------------------------------------------------------
*/

gulp.task("watch", ['bundle', 'lint:js'], function() {

    // Create LiveReload server
    livereload.listen(); // install Chrome livereload plugin :)

    // Watch styles
    // gulp.watch(path.join( paths.sass, "**", "*.scss"), ["css"]);
    gulp.watch(path.join(__dirname, "wagtail",  "wagtailadmin", "static-src", "**", "*.js" ), ["lint:js"]);

    // Watch any files in css path, reload on change
    //gulp.watch(path.join( paths.css, "**")).on('change', livereload.changed);

});

