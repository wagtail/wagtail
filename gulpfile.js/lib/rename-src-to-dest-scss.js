var path = require('path');
var rename = require('gulp-rename');
var config = require('../config');

/**
 * Returns a configured gulp-rename to pipe from asset sources to dest.
 * Usage: .pipe(renameSrcToDestScss())
 */
var renameSrcToDestScss = function(log) {
    return rename(function(filePath) {
        if (log) console.log(filePath.dirname + path.sep + filePath.basename + filePath.extname);
        filePath.dirname = filePath.dirname.replace(
            path.sep + config.srcDir + path.sep,
            path.sep + config.destDir + path.sep
        ).replace(path.sep + "scss", path.sep + "css");
        if (log) console.log(filePath.dirname);
    });
};

module.exports = renameSrcToDestScss;
