import { mergeRsbuildConfig } from '@rsbuild/core';
import { pluginReact } from '@rsbuild/plugin-react';
import { pluginSass } from '@rsbuild/plugin-sass';
import autoprefixer from 'autoprefixer';
import cssnano from 'cssnano';
import tailwindcss from 'tailwindcss';

const storybook = {
  stories: [
    '../../client/**/*.mdx',
    '../../client/**/*.stories.@(js|tsx)',
    '../../wagtail/**/*.@(mdx|stories.*)',
  ],

  addons: ['@storybook/addon-docs'],
  framework: { name: 'storybook-react-rsbuild', options: {} },

  rsbuildFinal: (config) =>
    mergeRsbuildConfig(config, {
      plugins: [pluginReact(), pluginSass({ rewriteUrls: false })],
      output: {
        // CSS is already minified by cssnano.
        minify: { css: false },
      },
      tools: {
        cssLoader: { url: false },
        // Vendor prefixes are already added by autoprefixer.
        lightningcssLoader: false,
        postcss: {
          postcssOptions: {
            plugins: [tailwindcss, autoprefixer, cssnano],
          },
        },
        rspack: (rspackConfig, { appendRules }) => {
          appendRules({ test: /\.(md|html)$/, type: 'asset/source' });

          // Allow using path magic variables to reduce boilerplate in stories.
          rspackConfig.node = { __filename: true, __dirname: true };
        },
      },
    }),

  typescript: {
    reactDocgen: 'react-docgen',
  },
};

export default storybook;
