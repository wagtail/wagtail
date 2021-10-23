var gulp = require("gulp");
var path = require("path");
var config = require("../config");

const paths = config.apps.reduce(
  (_, app) => ({
    "styles:sass": [
      ...(_["styles:sass"] || []),
      path.join(app.sourceFiles, "*/scss/**"),
    ],
    "styles:css": [
      ...(_["styles:css"] || []),
      path.join(app.sourceFiles, "*/css/**"),
    ],
    scripts: [...(_["scripts"] || []), path.join(app.sourceFiles, "*/js/**")],
    images: [...(_["images"] || []), path.join(app.sourceFiles, "*/images/**")],
    fonts: [...(_["fonts"] || []), path.join(app.sourceFiles, "*/fonts/**")],
  }),
  {}
);

paths["styles:sass"] = [...paths["styles:sass"], "./client/**/*.scss"];

var gulpOptions = {
  cwd: path.resolve("."),
};

/*
 * Watch - Watch files, trigger tasks when they are modified
 */
gulp.task(
  "watch",
  gulp.series("build", function (cb) {
    gulp.watch(paths["styles:sass"], gulpOptions, gulp.series("styles:sass"));
    gulp.watch(paths["styles:css"], gulpOptions, gulp.series("styles:css"));
    gulp.watch(paths["scripts"], gulpOptions, gulp.series("scripts"));
    gulp.watch(paths["images"], gulpOptions, gulp.series("images"));
    gulp.watch(paths["fonts"], gulpOptions, gulp.series("fonts"));
  })
);
