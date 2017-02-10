const path = require('path');
const glob = require('glob');
const webpack = require('webpack');

const COMMON_PATH = './wagtail/wagtailadmin/static/wagtailadmin/js/common.js';

function getEntryPoint(filename) {
  const appName = filename.split(path.sep)[2];
  const entryName = path.basename(filename, '.entry.js');
  const outputPath = path.join('wagtail', appName, 'static', appName, 'js', entryName);
  const entry = {};

  entry[outputPath] = ['whatwg-fetch', 'babel-polyfill', filename];

  return entry;
}

function entryPoints(globPath) {
  const paths = glob.sync(globPath);

  return paths.reduce((entries, p) => Object.assign(entries, getEntryPoint(p)), {});
}

module.exports = function exports() {
  return {
    entry: entryPoints('./wagtail/**/static_src/**/app/*.entry.js'),
    output: {
      path: './',
      filename: '[name].js',
      publicPath: '/static/js/'
    },
    plugins: [
      new webpack.optimize.CommonsChunkPlugin('common', COMMON_PATH, Infinity)
    ],
    module: {
      loaders: [
        {
          test: /\.js$/,
          loader: 'babel'
        },
      ]
    }
  };
};
