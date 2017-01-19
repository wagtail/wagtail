var _ = require('lodash');
var path = require('path');
var glob = require('glob').sync;
var webpack = require('webpack');

var COMMON_PATH = './wagtail/wagtailadmin/static/wagtailadmin/js/common.js';


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
  var CLIENT_DIR = path.resolve(__dirname, '..', 'src');

  return {
    entry: entryPoints('./wagtail/**/static_src/**/app/*.entry.js'),
    resolve: {
      alias: {
        config: path.resolve(CLIENT_DIR, 'config'),
        components: path.resolve(CLIENT_DIR, 'components')
      }
    },
    output: {
      path: './',
      filename: '[name].js',
      publicPath: '/static/js/'
    },
    plugins: [
      new webpack.ProvidePlugin({
        fetch: 'imports?this=>global!exports?global.fetch!whatwg-fetch'
      }),
      new webpack.optimize.CommonsChunkPlugin('common', COMMON_PATH, Infinity)
    ],
    module: {
      loaders: [
        {
          test: /\.js$/,
          loader: 'babel'
        },
        {
          test: /\.jsx$/,
          loader: 'babel'
        }
      ]
    }
  };
};
