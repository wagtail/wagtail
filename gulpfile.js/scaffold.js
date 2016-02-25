var path = require('path');
var fs = require('fs');
var Mustache = require('mustache');
var args = process.argv.slice(2);
var NAME = args[0];

if (!NAME) {
    console.error('No component name provided');
    process.exit();
    return;
}

var TEMPLATES = path.join('.', 'client', 'template');
var SLUG = slugify(NAME);
var shortPath = path.join('src', 'components', SLUG);
var directory = path.join('.', 'client', shortPath);

var files = [
    {
        name: 'index.js',
        template: 'component.mst'
    },
    {
        name: 'style.scss',
        template: 'style.mst'
    },
    {
        name: 'README.md',
        template: 'README.mst'
    }
];


// =============================================================================
// Helper methods
// =============================================================================

function slugify(text) {
    return text.toString().split(/(?=[A-Z])/).join('-').toLowerCase().trim()
    .replace(/\s+/g, '-')           // Replace spaces with -
    .replace(/&/g, '-and-')         // Replace & with 'and'
    .replace(/[^\w\-]+/g, '')       // Remove all non-word chars
    .replace(/\-\-+/g, '-');        // Replace multiple - with single -
}

function write(name, data) {
    fs.writeFile(name, data, function(err) {
        if (err) {
            return console.log('[ error ] ' + err);
        }
        console.log('[ created ] ' + name);
    });
};


// =============================================================================
// Write files!
// =============================================================================

if (!fs.existsSync(directory)) {
    fs.mkdirSync(directory);
} else {
    console.warn('[ error ] ' + directory + ' already exists');
    return;
}

files.forEach(function(file) {
    var template = fs.readFileSync(path.join(TEMPLATES, file.template), 'utf8');
    var newPath = path.join(directory, file.name);
    var context = {
        name: NAME,
        slug: SLUG
    };

    write(newPath, Mustache.render(template, context));
});
