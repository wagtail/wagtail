const baseConfig = require('./client/tailwind.config');

/**
 * Tailwind config file for Wagtail itself.
 */
module.exports = {
  presets: [baseConfig],
  content: [
    './wagtail/**/*.{py,html,ts,tsx}',
    './wagtail/**/static_src/**/*.js',
    // Make sure NOT to include the `client/scss` directory,
    // even if we don't specify `*.scss` files here.
    // The directory would still be scanned for files, which would cause
    // the styles to rebuild in a loop.
    // https://tailwindcss.com/docs/content-configuration#styles-rebuild-in-an-infinite-loop
    './client/src/**/*.{js,ts,tsx,mdx}',
    './docs/**/*.{md,rst}',
  ],
  corePlugins: {
    // Risk of clashing with existing styles.
    preflight: false,
  },
};
