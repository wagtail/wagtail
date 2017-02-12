const path = require('path');
const webpack = require('webpack');

// Generates a path to an entry file to be compiled by Webpack.
const getEntryPath = (app, filename) => path.resolve('wagtail', app, 'static_src', app, 'app', filename);
// Generates a path to the output bundle to be loaded in the browser.
const getOutputPath = (app, filename) => path.join('wagtail', app, 'static', app, 'js', filename);

const isVendorModule = (module) => {
  const res = module.resource;
  return res && res.indexOf('node_modules') >= 0 && res.match(/\.js$/);
};

module.exports = function exports() {
  const entry = {
    // Create a vendor chunk that will contain polyfills, and all third-party dependencies.
    vendor: ['whatwg-fetch', 'babel-polyfill'],
  };

  entry[getOutputPath('wagtailadmin', 'wagtailadmin')] = getEntryPath('wagtailadmin', 'wagtailadmin.entry.js');

  return {
    entry: entry,
    output: {
      path: '.',
      filename: '[name].js',
      publicPath: '/static/js/'
    },
    plugins: [
      new webpack.optimize.CommonsChunkPlugin({
        name: 'vendor',
        filename: getOutputPath('wagtailadmin', '[name].js'),
        minChunks: isVendorModule,
      }),
    ],
    resolve: {
      alias: {
        'wagtail-client': path.resolve('.', 'client'),
      },
    },
    module: {
      loaders: [
        {
          test: /\.js$/,
          loader: 'babel'
        },
      ]
    },
    stats: {
      // Add chunk information (setting this to `false` allows for a less verbose output)
      chunks: false,
      // Add the hash of the compilation
      hash: false,
      // `webpack --colors` equivalent
      colors: true,
      // Add information about the reasons why modules are included
      reasons: false,
      // Add webpack version information
      version: false,
    },
  };
};
