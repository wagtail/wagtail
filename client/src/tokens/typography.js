// Note: Tailwind does not automatically escape font names.
// If a font name contains an invalid identifier (like a space), we wrap it in quotes to escape the invalid characters.
// Font stack optimised for built-in fonts of each major operating system, with support for emojis.

const systemUIFontStack = [
  '-apple-system',
  'BlinkMacSystemFont',
  '"Segoe UI"',
  'system-ui',
  'Roboto',
  '"Helvetica Neue"',
  'Arial',
  'sans-serif',
  'Apple Color Emoji',
  '"Segoe UI Emoji"',
  '"Segoe UI Symbol"',
  '"Noto Color Emoji"',
];

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

// Key is equal to the pixel size of the rem value.
// These values are used in combinations create typography defaults
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

// These are set to ems to be relative to the font size
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

module.exports = {
  systemUIFontStack,
  monoFontStack,
  fontFamily,
  fontSize,
  fontWeight,
  letterSpacing,
  lineHeight,
};
