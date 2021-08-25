const path = require('path');

// Generates a path to the output bundle to be loaded in the browser.
const getOutputPath = (app, filename) => {
  let appLabel = `wagtail${app}`;

  // Exceptions
  if (app === 'documents') {
    appLabel = 'wagtaildocs';
  } else if (app === 'contrib/table_block') {
    appLabel = 'table_block';
  }

  return path.join('wagtail', app, 'static', appLabel, 'js', filename);
};

// Mapping from package name to exposed global variable.
const exposedDependencies = {
  'focus-trap-react': 'FocusTrapReact',
  'react': 'React',
  'react-dom': 'ReactDOM',
  'react-transition-group/CSSTransitionGroup': 'CSSTransitionGroup',
  'draft-js': 'DraftJS',
};

module.exports = function exports() {
  const entrypoints = {
    'admin': [
      'collapsible',
      'comments',
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
      'sidebar',
      'sidebar-legacy',
      'task-chooser-modal',
      'task-chooser',
      'telepath/blocks',
      'telepath/telepath',
      'telepath/widgets',
      'userbar',
      'wagtailadmin',
      'workflow-action',
      'workflow-status',
    ],
    'images': [
      'image-chooser',
      'image-chooser-telepath',
    ],
    'documents': [
      'document-chooser',
      'document-chooser-telepath',
    ],
    'snippets': [
      'snippet-chooser',
      'snippet-chooser-telepath',
    ],
    'contrib/table_block': [
      'table',
    ],
  };

  const entry = {};
  for (const [appName, moduleNames] of Object.entries(entrypoints)) {
    moduleNames.forEach(moduleName => {
      entry[moduleName] = {
        import: [`./client/src/entrypoints/${appName}/${moduleName}.js`],
        filename: getOutputPath(appName, moduleName) + '.js',
      };

      // Add polyfills to all bundles except userbar
      // polyfills.js imports from node_modules, which adds a dependency on vendor.js (produced by splitChunks)
      // Because userbar is supposed to run on peoples frontends, we code it using portable JS so we don't need
      // to pull in all the additional JS that the vendor bundle has (such as React).
      if (moduleName !== 'userbar') {
        entry[moduleName].import.push('./client/src/utils/polyfills.js');
      }
    });
  }

  return {
    entry: entry,
    output: {
      path: path.resolve('.'),
      publicPath: '/static/js/'
    },
    resolve: {
      extensions: ['.ts', '.tsx', '.js'],

      // Some libraries import Node modules but don't use them in the browser.
      // Tell Webpack to provide empty mocks for them so importing them works.
      fallback: {
        fs: false,
        net: false,
        tls: false,
      },
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
              options: {
                exposes: {
                  globalName,
                  override: true
                }
              },
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
    },
  };
};
