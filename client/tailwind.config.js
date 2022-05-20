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
  typeScale,
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
const scrollbarThin = require('./src/plugins/scrollbarThin');

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
      /* allow system colours https://www.w3.org/TR/css-color-4/#css-system-colors */
      LinkText: 'LinkText',
      ButtonText: 'ButtonText',
    },
    fontFamily: {
      sans: 'var(--w-font-sans)',
      mono: 'var(--w-font-mono)',
    },
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
    extend: {
      opacity: {
        15: '0.15',
        85: '0.85',
      },
      outlineOffset: {
        inside: '-3px',
      },
      transitionProperty: {
        sidebar:
          'inset-inline-start, padding-inline-start, width, transform, margin-top, min-height',
      },
      zIndex: {
        'header': '100',
        'sidebar': '110',
        'sidebar-toggle': '120',
        'dialog': '130',
      },
      keyframes: {
        'fade-in': {
          '0%': { opacity: 0 },
          '100%': { opacity: 1 },
        },
      },
      animation: {
        'fade-in': 'fade-in 150ms both',
      },
    },
  },
  plugins: [
    typeScale,
    vanillaRTL,
    scrollbarThin,
    /**
     * forced-colors media query for Windows High-Contrast mode support
     * See:
     * - https://developer.mozilla.org/en-US/docs/Web/CSS/@media/forced-colors
     * - https://github.com/tailwindlabs/tailwindcss/blob/v3.0.23/src/corePlugins.js#L168-L171
     */
    plugin(({ addVariant }) => {
      addVariant('forced-colors', '@media (forced-colors: active)');
    }),
    /**
     * TypeScale plugin.
     * This plugin generates component classes using tailwind's theme values for each object inside of the typeScale configuration.
     * We have the `w-` prefix added in the configuration for documentation purposes, it needs to be removed here before Tailwind adds it back.
     */
    plugin(({ addComponents, theme }) => {
      const scale = {};
      Object.entries(typeScale).forEach(([name, styles]) => {
        scale[`.${name.replace('w-', '')}`] = Object.fromEntries(
          Object.entries(styles).map(([key, value]) => [key, theme(value)]),
        );
      });
      addComponents(scale);
    }),
    /**
     * CSS Custom properties defined from our design tokens.
     */
    plugin(({ addBase }) => {
      addBase({
        ':root': {
          '--w-font-sans': fontFamily.sans.join(', '),
          '--w-font-mono': fontFamily.mono.join(', '),
        },
      });
    }),
  ],
  corePlugins: {
    ...vanillaRTL.disabledCorePlugins,
    // Disable float and clear which have poor RTL support.
    float: false,
    clear: false,
    // Disable text-transform so we don’t rely on uppercasing text.
    textTransform: false,
  },
  variants: {
    extend: {
      backgroundColor: ['forced-colors'],
      width: ['forced-colors'],
      height: ['forced-colors'],
    },
  },
};
