// Note: Tailwind does not automatically escape font names.
// If a font name contains an invalid identifier (lke a space), we wrap it in quotes to escape the invalid characters.
// Font stack optimised for built-in fonts of each major operating system, with support for emojis.
/** @type {SansFontStack[]} */
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

/** @type {monoFontStack[]} */
const monoFontStack = ['monospace', 'serif'];

const fontFamilies = {
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

module.exports = {
  systemUIFontStack,
  monoFontStack,
  fontFamilies,
  fontSize,
};
