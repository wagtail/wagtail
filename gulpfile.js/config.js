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

module.exports = {
    apps: apps,
    srcDir: srcDir,
    destDir: destDir
}