module.exports = {
  stories: [
    '../../client/**/*.stories.mdx',
    '../../client/**/*.stories.@(js|tsx)',
    {
      directory: '../../wagtail/admin/templates/wagtailadmin/shared/',
      titlePrefix: 'Shared',
      files: '*.stories.*',
    },
    '../../wagtail/**/*.stories.*',
  ],
  addons: ['@storybook/addon-docs', '@storybook/addon-controls'],
  framework: '@storybook/react',
  core: {
    builder: 'webpack5',
  },
  webpackFinal: (config) => {
    /* eslint-disable no-param-reassign */

    const rules = [
      {
        test: /\.(scss|css)$/,
        use: [
          'style-loader',
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
          'sass-loader',
        ],
      },
      {
        test: /\.(md|html)$/,
        type: 'asset/source',
      },
    ];

    config.module.rules = config.module.rules.concat(rules);

    // Allow using path magic variables to reduce boilerplate in stories.
    config.node = {
      __filename: true,
      __dirname: true,
    };

    return config;
  },
};
