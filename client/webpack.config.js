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
    'contrib/modeladmin': 'wagtailmodeladmin',
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
      'collapsible',
      'comments',
      'core',
      'date-time-chooser',
      'draftail',
      'expanding-formset',
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
      'bulk-actions',
    ],
    'images': ['image-chooser', 'image-chooser-telepath'],
    'documents': ['document-chooser', 'document-chooser-telepath'],
    'snippets': ['snippet-chooser', 'snippet-chooser-telepath'],
    'contrib/table_block': ['table'],
    'contrib/typed_table_block': ['typed_table_block'],
  };

  const entry = {};
  for (const [appName, moduleNames] of Object.entries(entrypoints)) {
    moduleNames.forEach((moduleName) => {
      entry[moduleName] = {
        import: [`./client/src/entrypoints/${appName}/${moduleName}.js`],
        filename: getOutputPath(appName, 'js', moduleName) + '.js',
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

  const sassEntry = {};
  sassEntry[getOutputPath('admin', 'css', 'core')] = path.resolve(
    'wagtail',
    'admin',
    'static_src',
    'wagtailadmin',
    'scss',
    'core.scss',
  );
  sassEntry[getOutputPath('admin', 'css', 'layouts/404')] = path.resolve(
    'wagtail',
    'admin',
    'static_src',
    'wagtailadmin',
    'scss',
    'layouts',
    '404.scss',
  );
  sassEntry[getOutputPath('admin', 'css', 'layouts/account')] = path.resolve(
    'wagtail',
    'admin',
    'static_src',
    'wagtailadmin',
    'scss',
    'layouts',
    'account.scss',
  );
  sassEntry[getOutputPath('admin', 'css', 'layouts/compare-revisions')] =
    path.resolve(
      'wagtail',
      'admin',
      'static_src',
      'wagtailadmin',
      'scss',
      'layouts',
      'compare-revisions.scss',
    );
  sassEntry[getOutputPath('admin', 'css', 'layouts/home')] = path.resolve(
    'wagtail',
    'admin',
    'static_src',
    'wagtailadmin',
    'scss',
    'layouts',
    'home.scss',
  );
  sassEntry[getOutputPath('admin', 'css', 'layouts/login')] = path.resolve(
    'wagtail',
    'admin',
    'static_src',
    'wagtailadmin',
    'scss',
    'layouts',
    'login.scss',
  );
  sassEntry[getOutputPath('admin', 'css', 'layouts/page-editor')] =
    path.resolve(
      'wagtail',
      'admin',
      'static_src',
      'wagtailadmin',
      'scss',
      'layouts',
      'page-editor.scss',
    );
  sassEntry[getOutputPath('admin', 'css', 'layouts/report')] = path.resolve(
    'wagtail',
    'admin',
    'static_src',
    'wagtailadmin',
    'scss',
    'layouts',
    'report.scss',
  );
  sassEntry[getOutputPath('admin', 'css', 'layouts/workflow-edit')] =
    path.resolve(
      'wagtail',
      'admin',
      'static_src',
      'wagtailadmin',
      'scss',
      'layouts',
      'workflow-edit.scss',
    );
  sassEntry[getOutputPath('admin', 'css', 'layouts/workflow-progress')] =
    path.resolve(
      'wagtail',
      'admin',
      'static_src',
      'wagtailadmin',
      'scss',
      'layouts',
      'workflow-progress.scss',
    );
  // sassEntry[getOutputPath('admin', 'css', 'normalize')] = path.resolve('wagtail', 'admin', 'static_src', 'wagtailadmin', 'css', 'normalize.css');
  sassEntry[getOutputPath('admin', 'css', 'panels/draftail')] = path.resolve(
    'wagtail',
    'admin',
    'static_src',
    'wagtailadmin',
    'scss',
    'panels',
    'draftail.scss',
  );
  sassEntry[getOutputPath('admin', 'css', 'panels/hallo')] = path.resolve(
    'wagtail',
    'admin',
    'static_src',
    'wagtailadmin',
    'scss',
    'panels',
    'hallo.scss',
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
  sassEntry[getOutputPath('admin', 'css', 'sidebar')] = path.resolve(
    'wagtail',
    'admin',
    'static_src',
    'wagtailadmin',
    'scss',
    'sidebar.scss',
  );
  sassEntry[getOutputPath('admin', 'css', 'userbar')] = path.resolve(
    'wagtail',
    'admin',
    'static_src',
    'wagtailadmin',
    'scss',
    'userbar.scss',
  );
  sassEntry[getOutputPath('documents', 'css', 'add-multiple')] = path.resolve(
    'wagtail',
    'documents',
    'static_src',
    'wagtaildocs',
    'scss',
    'add-multiple.scss',
  );
  sassEntry[getOutputPath('images', 'css', 'add-multiple')] = path.resolve(
    'wagtail',
    'images',
    'static_src',
    'wagtailimages',
    'scss',
    'add-multiple.scss',
  );
  sassEntry[getOutputPath('images', 'css', 'focal-point-chooser')] =
    path.resolve(
      'wagtail',
      'images',
      'static_src',
      'wagtailimages',
      'scss',
      'focal-point-chooser.scss',
    );
  sassEntry[getOutputPath('users', 'css', 'groups_edit')] = path.resolve(
    'wagtail',
    'users',
    'static_src',
    'wagtailusers',
    'scss',
    'groups_edit.scss',
  );
  sassEntry[getOutputPath('contrib/styleguide', 'css', 'styleguide')] =
    path.resolve(
      'wagtail',
      'contrib',
      'styleguide',
      'static_src',
      'wagtailstyleguide',
      'scss',
      'styleguide.scss',
    );
  sassEntry[getOutputPath('contrib/modeladmin', 'css', 'index')] = path.resolve(
    'wagtail',
    'contrib',
    'modeladmin',
    'static_src',
    'wagtailmodeladmin',
    'scss',
    'index.scss',
  );
  sassEntry[getOutputPath('contrib/modeladmin', 'css', 'breadcrumbs_page')] =
    path.resolve(
      'wagtail',
      'contrib',
      'modeladmin',
      'static_src',
      'wagtailmodeladmin',
      'scss',
      'breadcrumbs_page.scss',
    );
  sassEntry[getOutputPath('contrib/modeladmin', 'css', 'choose_parent_page')] =
    path.resolve(
      'wagtail',
      'contrib',
      'modeladmin',
      'static_src',
      'wagtailmodeladmin',
      'scss',
      'choose_parent_page.scss',
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
            from: 'wagtail/search/static_src/',
            to: 'wagtail/search/static/',
            globOptions: { ignore: ['**/{app,scss}/**', '*.{css,txt}'] },
          },
          {
            from: 'wagtail/snippets/static_src/',
            to: 'wagtail/snippets/static/',
            globOptions: { ignore: ['**/{app,scss}/**', '*.{css,txt}'] },
          },
          {
            from: 'wagtail/users/static_src/',
            to: 'wagtail/users/static/',
            globOptions: { ignore: ['**/{app,scss}/**', '*.{css,txt}'] },
          },
          {
            from: 'wagtail/contrib/settings/static_src/',
            to: 'wagtail/contrib/settings/static/',
            globOptions: { ignore: ['**/{app,scss}/**', '*.{css,txt}'] },
          },
          {
            from: 'wagtail/contrib/modeladmin/static_src/',
            to: 'wagtail/contrib/modeladmin/static/',
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
          // Legacy support for font icon loading, to be removed.
          test: /\.(woff)$/i,
          generator: {
            emit: false,
            filename: 'wagtailadmin/fonts/[name][ext]',
          },
        },
        {
          test: /\.(svg)$/i,
          type: 'asset/inline',
        },
        {
          test: /\.(scss|css)$/,
          use: [
            MiniCssExtractPlugin.loader,
            'css-loader',
            {
              loader: 'postcss-loader',
              options: {
                postcssOptions: {
                  plugins: ['autoprefixer', 'cssnano'],
                },
              },
            },
            'sass-loader',
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
