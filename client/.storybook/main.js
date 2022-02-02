module.exports = {
  stories: ['../src/**/*.stories.@(js|jsx|ts|tsx)'],
  core: {
    builder: 'webpack5',
  },
  webpackFinal: (config) => {
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
    ];

    config.module.rules = config.module.rules.concat(rules);

    return config;
  },
};
