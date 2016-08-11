var base = require('./webpack.base.config');
var config = base('development');


// development overrides go here
config.watch = true;
config.devtool = 'cheap-module-eval-source-map';

module.exports = config;
