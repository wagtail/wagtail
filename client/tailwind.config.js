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
  plugins: [typeScale],
  corePlugins: {},
};
