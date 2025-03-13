const plugin = require('tailwindcss/plugin');
const vanillaRTL = require('tailwindcss-vanilla-rtl');
/**
 * Design Tokens
 */
const { staticColors, transparencies } = require('./src/tokens/colors');
const {
  generateColorVariables,
  generateThemeColorVariables,
} = require('./src/tokens/colorVariables');
const colorThemes = require('./src/tokens/colorThemes');
const {
  fontFamily,
  fontSize,
  fontWeight,
  letterSpacing,
  lineHeight,
  listStyleType,
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
  Object.entries(staticColors).map(([key, hues]) => {
    const shades = Object.fromEntries(
      Object.entries(hues).map(([k, shade]) => [
        k,
        `var(${shade.cssVariable})`,
      ]),
    );
    return [key, shades];
  }),
);

const lightThemeColors = colorThemes.light.reduce((colorTokens, category) => {
  Object.entries(category.tokens).forEach(([name, token]) => {
    // eslint-disable-next-line no-param-reassign
    colorTokens[name] = `var(${token.cssVariable})`;
  });
  return colorTokens;
}, {});

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
      ...lightThemeColors,
      'white-10': 'var(--w-color-white-10)',
      'white-15': 'var(--w-color-white-15)',
      'white-50': 'var(--w-color-white-50)',
      'white-80': 'var(--w-color-white-80)',
      'black-5': 'var(--w-color-black-5)',
      'black-10': 'var(--w-color-black-10)',
      'black-20': 'var(--w-color-black-20)',
      'black-25': 'var(--w-color-black-25)',
      'black-35': 'var(--w-color-black-35)',
      'black-50': 'var(--w-color-black-50)',
      // Color keywords.
      'inherit': 'inherit',
      'current': 'currentColor',
      'transparent': 'transparent',
      /* allow system colours https://www.w3.org/TR/css-color-4/#css-system-colors */
      'LinkText': 'LinkText',
      'ButtonText': 'ButtonText',
    },
    fontFamily: {
      sans: 'var(--w-font-sans)',
      mono: 'var(--w-font-mono)',
    },
    fontSize,
    fontWeight,
    lineHeight,
    listStyleType,
    letterSpacing,
    borderRadius,
    borderWidth,
    boxShadow: {
      ...boxShadow,
      none: 'none',
    },
    spacing: {
      ...spacing,
      'slim-header': '50px',
    },
    extend: {
      outlineOffset: {
        inside: '-3px',
      },
      transitionProperty: {
        sidebar:
          'inset-inline-start, padding-inline-start, width, transform, margin-top, min-height',
      },
      zIndex: {
        'minimap': '80',
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
        /** Support for web components */
        ':root, :host': {
          '--w-font-sans': fontFamily.sans.join(', '),
          '--w-font-mono': fontFamily.mono.join(', '),
          '--w-density-factor': '1',
          ...transparencies,
          ...generateColorVariables(staticColors),
          ...generateThemeColorVariables(colorThemes.light),
          'color-scheme': 'light',
        },
        '.w-theme-system': {
          '@media (prefers-color-scheme: dark)': {
            ...generateThemeColorVariables(colorThemes.dark),
            'color-scheme': 'dark',
          },
        },
        '.w-theme-dark': {
          ...generateThemeColorVariables(colorThemes.dark),
          'color-scheme': 'dark',
        },
        '.w-density-snug': {
          '--w-density-factor': '0.5',
        },
      });
    }),
    /** Support for aria-expanded=true variant */
    plugin(({ addVariant }) => {
      addVariant('expanded', '&[aria-expanded=true]');
    }),
    /** Support for increased contrast theme */
    plugin(({ addVariant }) => {
      addVariant('more-contrast', [
        '.contrast-more &',
        '@media (prefers-contrast: more) { .contrast-system & }',
      ]);
    }),
  ],
  corePlugins: {
    ...vanillaRTL.disabledCorePlugins,
    // Disable float and clear. Use Flexbox or Grid instead.
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
