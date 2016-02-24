var _ = require('lodash');
var path = require('path');
var glob = require('glob').sync;


module.exports = function(env) {
    return {
        entry: entryPoints('./wagtail/**/static_src/**/app/*.entry.js'),
        output: {
          path: './',
          filename: '[name].js'
        },
        module: {
            loaders: [{
                test: /\.js$/,
                loader: 'babel',
            }, {
                test: /\.jsx$/,
                loader: 'babel',
            }]
        },
    };
};


function entryPoints(paths) {
    return _(glob(paths))
        .map(entryPoint)
        .fromPairs()
        .value();
}


function entryPoint(filename) {
    var name = appName(filename);
    var entryName = path.basename(filename, '.entry.js');
    var outputPath = path.join('wagtail', name, 'static', name, 'js', entryName);
    return [outputPath, filename];
}


function appName(filename) {
    return _(filename)
        .split(path.sep)
        .get(2);
}
