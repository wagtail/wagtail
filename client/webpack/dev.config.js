var webpack = require('webpack');
var base = require('./base.config');
var config = base('development');


// development overrides go here
config.watch = true;
// See http://webpack.github.io/docs/configuration.html#devtool
config.devtool = 'inline-source-map';

// Set process.env.NODE_ENV to development to enable JS development aids.
config.plugins.push(new webpack.DefinePlugin({
  'process.env': {
    NODE_ENV: JSON.stringify('development'),
  },
}));

module.exports = config;
