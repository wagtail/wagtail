var webpack = require('webpack');
var base = require('./base.config');
const UglifyJsPlugin = require('uglifyjs-webpack-plugin');
var config = base('production');


// production overrides go here
config.plugins = [new webpack.DefinePlugin({
  'process.env': {
    NODE_ENV: JSON.stringify('production'),
  },
})];

// See https://github.com/facebookincubator/create-react-app/blob/master/packages/react-scripts/config/webpack.config.prod.js.
config.optimization.minimizer = [
  new UglifyJsPlugin({
    sourceMap: true,
    uglifyOptions: {
      compress: {
        warnings: false,
      },
      mangle: true,
      ie8: false,
      output: {
        comments: false,
      },
    },
  })
];

module.exports = config;
