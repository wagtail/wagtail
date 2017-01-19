var webpack = require('webpack');
var base = require('./base.config');
var config = base('production');


// production overrides go here
config.plugins.push(new webpack.DefinePlugin({
  'process.env': {
    NODE_ENV: JSON.stringify('production'),
  },
}));

// See https://github.com/facebookincubator/create-react-app/blob/master/packages/react-scripts/config/webpack.config.prod.js.
config.plugins.push(new webpack.optimize.UglifyJsPlugin({
  compress: {
    screw_ie8: true,
    warnings: false
  },
  mangle: {
    screw_ie8: true
  },
  output: {
    comments: false,
    screw_ie8: true
  },
}));

module.exports = config;
