const plugin = require('tailwindcss/plugin');
const vanillaRTL = require('tailwindcss-vanilla-rtl');

/**
 * Design Tokens
 */
const colors = require('./src/tokens/colors');
const {
  fontFamily,
  fontSize,
  fontWeight,
  letterSpacing,
  lineHeight,
} = require('./src/tokens/typography');
const { breakpoints } = require('./src/tokens/breakpoints');
const {
  borderRadius,
  borderWidth,
  boxShadow,
} = require('./src/tokens/objectStyles');
const { spacing } = require('./src/tokens/spacing');

/**
 * Plugins
 */
const typeScale = require('./src/tokens/typeScale');

/**
 * Functions
 * themeColors: For converting our design tokens into a format that tailwind accepts
 */
const themeColors = Object.fromEntries(
  Object.entries(colors).map(([key, hues]) => {
    const shades = Object.fromEntries(
      Object.entries(hues).map(([k, shade]) => [k, shade.hex]),
    );
    return [key, shades];
  }),
);

/**
 * Root Tailwind config, reusable for other projects.
 */
module.exports = {
  prefix: 'w-',
  theme: {
    screens: {
      ...breakpoints,
    },
    colors: {
      ...themeColors,
      inherit: 'inherit',
      current: 'currentColor',
      transparent: 'transparent',
      LinkText: 'LinkText',
      ButtonText: 'ButtonText',
    },
    fontFamily,
    fontSize,
    fontWeight,
    lineHeight,
    letterSpacing,
    borderRadius,
    borderWidth,
    boxShadow: {
      ...boxShadow,
      none: 'none',
    },
    spacing,
  },
  plugins: [
    typeScale,
    vanillaRTL,
    /**
     * forced-colors media query for Windows High-Contrast mode support
     * See:
     * - https://developer.mozilla.org/en-US/docs/Web/CSS/@media/forced-colors
     * - https://github.com/tailwindlabs/tailwindcss/blob/7b4cc36f5ea1f7e208dcd3af3e8288878735f45f/src/corePlugins.js#L169-L172
     */
    plugin(({ addVariant }) => {
      addVariant('forced-colors', '@media (forced-colors: active)');
    }),
  ],
  corePlugins: {
    ...vanillaRTL.disabledCorePlugins,
    // Disable float and clear which have poor RTL support.
    float: false,
    clear: false,
  },
};
