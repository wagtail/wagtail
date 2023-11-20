module.exports = {
  stories: [
    '../../client/**/*.stories.mdx',
    '../../client/**/*.stories.@(js|tsx)',
    '../../wagtail/**/*.stories.*',
  ],

  addons: ['@storybook/addon-docs', '@storybook/addon-controls'],

  framework: {
    name: '@storybook/react-webpack5',
    options: {},
  },

  // Redefine Babel config to allow TypeScript class fields `declare`.
  // See https://github.com/storybookjs/storybook/issues/12479.
  // The resulting configuration is closer to Wagtail’s Webpack + TypeScript setup,
  // preventing other potential issues with JS transpilation differences.
  babel: async (options) => ({
    ...options,
    plugins: [],
    presets: [
      ['@babel/preset-typescript', { allowDeclareFields: true }],
      ['@babel/preset-react', { runtime: 'automatic' }],
    ],
  }),

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

  docs: {
    autodocs: true,
  },
};
