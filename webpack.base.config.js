var _ = require('lodash');
var path = require('path');
var glob = require('glob').sync;


function appName(filename) {
  return _(filename)
    .split(path.sep)
    .get(2);
}


function entryPoint(filename) {
  var name = appName(filename);
  var entryName = path.basename(filename, '.entry.js');
  var outputPath = path.join('wagtail', name, 'static', name, 'js', entryName);
  return [outputPath, filename];
}


function entryPoints(paths) {
  return _(glob(paths))
    .map(entryPoint)
    .fromPairs()
    .value();
}


module.exports = function exports() {
  return {
    entry: entryPoints('./wagtail/**/static_src/**/app/*.entry.js'),
    resolve: {
      alias: {
        wagtail: path.join(__dirname, 'client/src/index.js')
      }
    },
    output: {
      path: './',
      filename: '[name].js'
    },
    module: {
      loaders: [{
        test: /\.js$/,
        loader: 'babel',
      }, {
        test: /\.jsx$/,
        loader: 'babel',
      }]
    },
  };
};
