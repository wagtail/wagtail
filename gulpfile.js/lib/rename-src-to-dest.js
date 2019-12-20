var rename = require('gulp-rename');
var config = require('../config');
var normalizePath = require('../lib/normalize-path');

/**
 * Returns a configured gulp-rename to pipe from asset sources to dest.
 * Usage: .pipe(renameSrcToDest())
 */
var renameSrcToDest = function(log) {
    return rename(function(filePath) {
        if (log) console.log(filePath.dirname + '/' + filePath.basename + filePath.extname);
        filePath.dirname = normalizePath(filePath.dirname).replace(
            '/' + config.srcDir + '/',
            '/' + config.destDir + '/');
        if (log) console.log(filePath.dirname);
    });
};

module.exports = renameSrcToDest;
