/**
 * # Typography
 * Note: Tailwind does not automatically escape font names.
 * If a font name contains an invalid identifier (like a space), we wrap it in quotes to escape the invalid characters.
 */

/**
 * System UI Font stack for primary usage.
 * Optimised for built-in fonts of each major operating system, with support for emojis.
 */
const systemUIFontStack = [
  // iOS Safari, macOS Safari, macOS Firefox
  '-apple-system',
  // macOS Chrome
  'BlinkMacSystemFont',
  // Windows - for all browsers on Windows 7+ (putting Segoe UI before system-ui ensures Segoe UI will be rendered for different languages)
  '"Segoe UI"',
  'system-ui',
  // Targets Android and newer Chrome OS'. (If Roboto is installed on your windows computer Segoe UI will take precedence.)
  'Roboto',
  // A common fallback font for older macOS'
  '"Helvetica Neue"',
  // Very old Windows versions (special shout-out to whoever is using windows 95)
  'Arial',
  // A last resort if all else fails, just give us something without serifs :)
  'sans-serif',
  // All the emojis 👋🙂
  'Apple Color Emoji',
  '"Segoe UI Emoji"',
  '"Segoe UI Symbol"',
  '"Noto Color Emoji"',
];

/**
 * System UI Font stack for mono-space usage.
 * Optimised for built-in fonts of each major operating system, with support for emojis.
 */
const monoFontStack = [
  // iOS Safari, MacOS Safari
  'ui-monospace',
  'Menlo',
  'Monaco',
  // Windows,
  '"Cascadia Mono"',
  '"Segoe UI Mono"',
  // Linux
  '"Roboto Mono"',
  '"Oxygen Mono"',
  '"Ubuntu Monospace"',
  // Android
  '"Source Code Pro"',
  // Firefox
  '"Fira Mono"',
  // Last resort Android/others
  '"Droid Sans Mono"',
  '"Courier New"',
  'monospace',
  // All the emojis 👋🙂
  '"Apple Color Emoji"',
  '"Segoe UI Emoji"',
  '"Segoe UI Symbol"',
  '"Noto Color Emoji"',
];

const fontFamily = {
  sans: systemUIFontStack,
  mono: monoFontStack,
};

/**
 * Key is equal to the pixel size of the rem value.
 * These values are used in combinations create typography defaults
 */
const fontSize = {
  14: '0.875rem',
  15: '0.9375rem',
  16: '1rem',
  18: '1.125rem',
  22: '1.375rem',
  24: '1.5rem',
  26: '1.625rem',
  30: '1.875rem',
};

const fontWeight = {
  normal: 400,
  medium: 500,
  semibold: 600,
  bold: 700,
  extrabold: 800,
};

/**
 * These are set to ems to be relative to the font size.
 */
const letterSpacing = {
  tighter: '-0.05em',
  tight: '-0.025em',
  normal: '0em',
  wide: '0.025em',
  wider: '0.05em',
  widest: '0.1em',
};

const lineHeight = {
  none: '1',
  tight: '1.3',
  normal: '1.5',
};

const headingBaseStyles = {
  fontWeight: 'fontWeight.bold',
  color: 'colors.primary.DEFAULT',
  lineHeight: 'lineHeight.tight',
};

/**
 * Wagtail’s type scale styles, written with Tailwind theme function values,
 * but in vanilla JS so the type scale can be reused outside of Tailwind.
 */
const typeScale = {
  'w-h1': {
    fontSize: 'fontSize.30',
    fontWeight: 'fontWeight.extrabold',
    color: 'colors.primary.DEFAULT',
    lineHeight: 'lineHeight.tight',
  },
  'w-h2': {
    fontSize: 'fontSize.24',
    ...headingBaseStyles,
  },
  'w-h3': {
    fontSize: 'fontSize.22',
    ...headingBaseStyles,
  },
  'w-h4': {
    fontSize: 'fontSize.18',
    ...headingBaseStyles,
  },
  'w-label-1': {
    fontSize: 'fontSize.16',
    fontWeight: 'fontWeight.bold',
    color: 'colors.primary.DEFAULT',
    lineHeight: 'lineHeight.tight',
  },
  'w-label-2': {
    fontSize: 'fontSize.15',
    fontWeight: 'fontWeight.semibold',
    color: 'colors.primary.DEFAULT',
    lineHeight: 'lineHeight.tight',
  },
  'w-label-3': {
    fontSize: 'fontSize.14',
    fontWeight: 'fontWeight.medium',
    color: 'colors.primary.DEFAULT',
    lineHeight: 'lineHeight.tight',
  },
  'w-body-text': {
    fontSize: 'fontSize.16',
    fontWeight: 'fontWeight.normal',
    lineHeight: 'lineHeight.normal',
  },
  'w-body-text-large': {
    fontSize: 'fontSize.18',
    fontWeight: 'fontWeight.normal',
    lineHeight: 'lineHeight.normal',
  },
  'w-help-text': {
    fontSize: 'fontSize.14',
    fontWeight: 'fontWeight.normal',
    color: 'colors.grey.400',
    lineHeight: 'lineHeight.tight',
  },
};

module.exports = {
  systemUIFontStack,
  monoFontStack,
  fontFamily,
  fontSize,
  fontWeight,
  letterSpacing,
  lineHeight,
  typeScale,
};
