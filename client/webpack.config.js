const path = require('path');

// Generates a path to the output bundle to be loaded in the browser.
const getOutputPath = (app, filename) => path.join('wagtail', app, 'static', `wagtail${app}`, 'js', filename);

// Mapping from package name to exposed global variable.
const exposedDependencies = {
  'focus-trap-react': 'FocusTrapReact',
  'react': 'React',
  'react-dom': 'ReactDOM',
  'react-transition-group/CSSTransitionGroup': 'CSSTransitionGroup',
  'draft-js': 'DraftJS',
};

module.exports = function exports() {
  const entrypoints = [
    'blocks/list',
    'blocks/sequence',
    'blocks/stream',
    'blocks/struct',
    'core',
    'date-time-chooser',
    'draftail',
    'expanding_formset',
    'filtered-select',
    'hallo-bootstrap',
    'hallo-plugins/hallo-hr',
    'hallo-plugins/hallo-requireparagraphs',
    'hallo-plugins/hallo-wagtaillink',
    'lock-unlock-action',
    'modal-workflow',
    'page-chooser-modal',
    'page-chooser',
    'page-editor',
    'privacy-switch',
    'task-chooser-modal',
    'task-chooser',
    'userbar',
    'wagtailadmin',
    'workflow-action',
    'workflow-status',
  ];

  const entry = {};
  entrypoints.forEach(moduleName => {
    entry[getOutputPath('admin', moduleName)] = [
      './client/src/utils/polyfills.js',
      `./client/src/entrypoints/${moduleName}.js`,
    ];
  });

  return {
    entry: entry,
    output: {
      path: path.resolve('.'),
      filename: '[name].js',
      publicPath: '/static/js/'
    },
    resolve: {
      extensions: ['.ts', '.tsx', '.js'],
    },
    externals: {
      jquery: 'jQuery',
    },
    module: {
      rules: [
        {
          test: /\.(js|ts)x?$/,
          loader: 'ts-loader',
          exclude: /node_modules/,
        },
      ].concat(Object.keys(exposedDependencies).map((name) => {
        const globalName = exposedDependencies[name];

        // Create expose-loader configs for each Wagtail dependency.
        return {
          test: require.resolve(name),
          use: [
            {
              loader: 'expose-loader',
              options: globalName,
            },
          ],
        };
      }))
    },

    optimization: {
      splitChunks: {
        cacheGroups: {
          vendor: {
            name: getOutputPath('admin', 'vendor'),
            chunks: 'initial',
            minChunks: 2,
            reuseExistingChunk: true,
          },
        },
      },
    },

    // See https://webpack.js.org/configuration/devtool/.
    devtool: 'source-map',

    // For development mode only.
    watchOptions: {
      poll: 1000,
      aggregateTimeout: 300,
    },

    // Disable performance hints – currently there are much more valuable
    // optimizations for us to do outside of Webpack
    performance: {
      hints: false
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
