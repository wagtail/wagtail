var webpack = require('webpack');
var base = require('./webpack.base.config');
var config = base('production');


// production overrides go here
config.watch = false;

config.plugins.push(new webpack.DefinePlugin({
  'process.env': {
    NODE_ENV: JSON.stringify('production'),
  },
}));

config.plugins.push(new webpack.optimize.UglifyJsPlugin({
  compress: {
    warnings: false,
  },
}));

module.exports = config;
