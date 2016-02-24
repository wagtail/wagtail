var _ = require('lodash');
var path = require('path');
var glob = require('glob').sync;
var webpack = require('webpack');


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
    output: {
      path: './',
      filename: '[name].js'
    },
    plugins: [
      new webpack.ProvidePlugin({
        'fetch': 'imports?this=>global!exports?global.fetch!whatwg-fetch'
      })
    ],
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
