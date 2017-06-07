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
    vendor: [
      './client/src/utils/polyfills.js',
    ],
  };

  entry[getOutputPath('wagtailadmin', 'wagtailadmin')] = getEntryPath('wagtailadmin', 'wagtailadmin.entry.js');

  return {
    entry: entry,
    output: {
      path: path.resolve('.'),
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
      rules: [
        {
          test: /\.js$/,
          loader: 'babel-loader',
          exclude: /node_modules/,
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
      // Set the maximum number of modules to be shown
      maxModules: 0,
    },
    // Some libraries import Node modules but don't use them in the browser.
    // Tell Webpack to provide empty mocks for them so importing them works.
    node: {
      fs: 'empty',
      net: 'empty',
      tls: 'empty',
    },
  };
};
