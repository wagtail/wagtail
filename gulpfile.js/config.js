var path = require('path');

var srcDir = 'static_src';
var destDir = 'static';

var App = function(dir, options) {
    this.dir = dir;
    this.options = options || {};
    this.appName = this.options.appName || path.basename(dir);
    this.sourceFiles = path.join('.', this.dir, srcDir);
};
App.prototype = Object.create(null);
App.prototype.scssIncludePaths = function() {
    return [this.sourceFiles];
};
App.prototype.scssSources = function() {
    // Assume that any scss we care about is always within the expected 
    // "appname/static_url/appname/scss/" folder.
    // NB: this requires the user to adhere to sass's underscore prefixing
    // to tell the compiler what files are includes.
    return path.join(this.sourceFiles, this.appName, '/scss/**/*.scss')
};

// All the Wagtail apps that contain static files
var apps = [
    new App('wagtail/wagtailadmin'),
    new App('wagtail/wagtaildocs'),
    new App('wagtail/wagtailembeds'),
    new App('wagtail/wagtailimages'),
    new App('wagtail/wagtailsnippets'),
    new App('wagtail/wagtailusers'),
    new App('wagtail/contrib/wagtailstyleguide'),
    new App('wagtail/contrib/settings', {
        'appName': 'wagtailsettings',
    }),
];

module.exports = {
    apps: apps,
    srcDir: srcDir,
    destDir: destDir
}
