const path = require('path');
const CopyPlugin = require('copy-webpack-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');

// Generates a path to the output bundle to be loaded in the browser.
const getOutputPath = (app, folder, filename) => {
  const exceptions = {
    'documents': 'wagtaildocs',
    'contrib/table_block': 'table_block',
    'contrib/typed_table_block': 'typed_table_block',
    'contrib/styleguide': 'wagtailstyleguide',
  };

  const appLabel = exceptions[app] || `wagtail${app}`;

  return path.join('wagtail', app, 'static', appLabel, folder, filename);
};

// Mapping from package name to exposed global variable.
const exposedDependencies = {
  'focus-trap-react': 'FocusTrapReact',
  'react': 'React',
  'react-dom': 'ReactDOM',
  'react-transition-group/CSSTransitionGroup': 'CSSTransitionGroup',
  'draft-js': 'DraftJS',
};

module.exports = function exports(env, argv) {
  const isProduction = argv.mode === 'production';

  const entrypoints = {
    'admin': [
      'chooser-modal',
      'chooser-widget',
      'chooser-widget-telepath',
      'comments',
      'core',
      'date-time-chooser',
      'draftail',
      'filtered-select',
      'icons',
      'modal-workflow',
      'page-chooser-modal',
      'page-chooser',
      'page-chooser-telepath',
      'privacy-switch',
      'sidebar',
      'task-chooser-modal',
      'task-chooser',
      'telepath/blocks',
      'telepath/telepath',
      'telepath/widgets',
      'userbar',
      'wagtailadmin',
      'workflow-action',
      'bulk-actions',
    ],
    'images': [
      'image-chooser',
      'image-chooser-modal',
      'image-chooser-telepath',
      'image-block',
    ],
    'documents': [
      'document-chooser',
      'document-chooser-modal',
      'document-chooser-telepath',
    ],
    'snippets': ['snippet-chooser', 'snippet-chooser-telepath'],
    'contrib/table_block': ['table'],
    'contrib/typed_table_block': ['typed_table_block'],
  };

  const entry = {};
  // eslint-disable-next-line no-restricted-syntax
  for (const [appName, moduleNames] of Object.entries(entrypoints)) {
    moduleNames.forEach((moduleName) => {
      entry[moduleName] = {
        import: [`./client/src/entrypoints/${appName}/${moduleName}.js`],
        filename: getOutputPath(appName, 'js', moduleName) + '.js',
      };
    });
  }

  const sassEntry = {};
  sassEntry[getOutputPath('admin', 'css', 'core')] = path.resolve(
    'wagtail',
    'admin',
    'static_src',
    'wagtailadmin',
    'scss',
    'core.scss',
  );
  sassEntry[getOutputPath('admin', 'css', 'panels/draftail')] = path.resolve(
    'wagtail',
    'admin',
    'static_src',
    'wagtailadmin',
    'scss',
    'panels',
    'draftail.scss',
  );
  sassEntry[getOutputPath('admin', 'css', 'panels/streamfield')] = path.resolve(
    'wagtail',
    'admin',
    'static_src',
    'wagtailadmin',
    'scss',
    'panels',
    'streamfield.scss',
  );
  sassEntry[
    getOutputPath('contrib/typed_table_block', 'css', 'typed_table_block')
  ] = path.resolve(
    'wagtail',
    'contrib',
    'typed_table_block',
    'static_src',
    'typed_table_block',
    'scss',
    'typed_table_block.scss',
  );

  return {
    entry: {
      ...entry,
      ...sassEntry,
    },
    output: {
      path: path.resolve('.'),
      publicPath: '/static/',
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

    plugins: [
      new MiniCssExtractPlugin({
        filename: '[name].css',
      }),
      new CopyPlugin({
        patterns: [
          {
            from: 'wagtail/admin/static_src/',
            to: 'wagtail/admin/static/',
            globOptions: { ignore: ['**/{app,scss}/**', '*.{css,txt}'] },
          },
          {
            from: 'wagtail/documents/static_src/',
            to: 'wagtail/documents/static/',
            globOptions: { ignore: ['**/{app,scss}/**', '*.{css,txt}'] },
          },
          {
            from: 'wagtail/embeds/static_src/',
            to: 'wagtail/embeds/static/',
            globOptions: { ignore: ['**/{app,scss}/**', '*.{css,txt}'] },
          },
          {
            from: 'wagtail/images/static_src/',
            to: 'wagtail/images/static/',
            globOptions: { ignore: ['**/{app,scss}/**', '*.{css,txt}'] },
          },
          {
            from: 'wagtail/contrib/search_promotions/static_src/',
            to: 'wagtail/contrib/search_promotions/static/',
            globOptions: { ignore: ['**/{app,scss}/**', '*.{css,txt}'] },
          },
        ],
      }),
    ],

    module: {
      rules: [
        {
          test: /\.(js|ts)x?$/,
          loader: 'ts-loader',
          exclude: /node_modules/,
        },
        {
          test: /\.(svg)$/i,
          type: 'asset/inline',
        },
        {
          test: /\.(scss|css)$/,
          use: [
            MiniCssExtractPlugin.loader,
            {
              loader: 'css-loader',
              options: {
                url: false,
              },
            },
            {
              loader: 'postcss-loader',
              options: {
                postcssOptions: {
                  plugins: ['tailwindcss', 'autoprefixer', 'cssnano'],
                },
              },
            },
            {
              loader: 'sass-loader',
              options: {
                sassOptions: {
                  // Manually set Sass output so it’s identical in production and development. See:
                  // https://github.com/tailwindlabs/tailwindcss/issues/11027
                  // https://github.com/webpack-contrib/sass-loader/issues/1129
                  style: 'expanded',
                },
              },
            },
          ],
        },
      ].concat(
        Object.keys(exposedDependencies).map((name) => {
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
                    override: true,
                  },
                },
              },
            ],
          };
        }),
      ),
    },

    optimization: {
      splitChunks: {
        cacheGroups: {
          vendor: {
            name: getOutputPath('admin', 'js', 'vendor'),
            chunks: 'initial',
            minChunks: 2,
            reuseExistingChunk: true,
          },
        },
      },
    },

    // See https://webpack.js.org/configuration/devtool/.
    devtool: isProduction ? false : 'eval-cheap-module-source-map',

    // For development mode only.
    watchOptions: {
      poll: 1000,
      aggregateTimeout: 300,
    },

    // Disable performance hints – currently there are much more valuable
    // optimizations for us to do outside of Webpack
    performance: {
      hints: false,
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
