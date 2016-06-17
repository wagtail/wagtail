var path = require('path');
var fs = require('fs');
var Mustache = require('mustache');

var TEMPLATES = path.join(__dirname, '..', '..', 'template');

var files = [
{
  name: 'component.js',
  template: 'component.mst',
  suffix: '.js',
},
{
  name: 'style.scss',
  template: 'style.mst'
},
{
  name: 'README.md',
  template: 'README.mst'
},
{
  name: 'component.test.js',
  template: 'component.test.mst',
  suffix: '.test.js',
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
}


// =============================================================================
// Write files!
// =============================================================================
function run(argv) {
  var name = argv.name[0].toUpperCase() + argv.name.substring(1);
  var slug = slugify(name);
  var directory = path.join(argv.dir, slug);

  if (!fs.existsSync(directory)) {
    fs.mkdirSync(directory);
  } else {
    console.warn('[ error ] ' + directory + ' already exists');
    return;
  }

  files.forEach(function(file) {
    var fileName = file.suffix ? name + file.suffix : file.name;
    var template = fs.readFileSync(path.join(TEMPLATES, file.template), 'utf8');
    var newPath = path.join(directory, fileName);
    var context = {
      name: name,
      slug: slug
    };

    write(newPath, Mustache.render(template, context));
  });
}


function build(cli) {
  return cli
    .option('dir', {
      default: process.env.PWD
    });
}


exports.handler = run;
exports.builder = build;
