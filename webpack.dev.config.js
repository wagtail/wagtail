var base = require('./webpack.base.config');
var config = base('development');


// development overrides go here
config.watch = true;

module.exports = config;
