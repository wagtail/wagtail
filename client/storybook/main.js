module.exports = {
  stories: ['../../client/**/*.stories.*', '../../wagtail/**/*.stories.*'],
  addons: ['@storybook/addon-docs'],
  core: {
    builder: 'webpack5',
  },
  webpackFinal: (config) => {
    /* eslint-disable no-param-reassign */
    config.resolve.fallback.crypto = false;

    const rules = [
      {
        test: /\.(scss|css)$/,
        use: [
          'style-loader',
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
      {
        test: /\.(md|html)$/,
        type: 'asset/source',
      },
    ];

    config.module.rules = config.module.rules.concat(rules);

    config.node = {
      __filename: true,
      __dirname: true,
    };

    return config;
  },
};
