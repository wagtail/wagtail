var base = require('./webpack.base.config');
var config = base('development');


// development overrides go here
config.watch = true;
// See http://webpack.github.io/docs/configuration.html#devtool
config.devtool = 'inline-source-map';

module.exports = config;
