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

// Key is equal to the pixel size of the rem value.
// These values are used in combinations create typography defaults
const fontSize = {
  14: '0.875rem', // 14px
  15: '0.9375rem', // 15px
  16: '1rem', // 16px
  18: '1.125rem', // 18px
  22: '1.1.375', // 22px
  24: '1.5rem', // 24px
  26: '1.625rem', // 26px
  30: '1.875rem', // 30px
};

// TODO: Create a plugin to convert these to tailwind variables with prefix w-h1, w-h2 etc
const typeScale = {
  'h1': { sm: 26, md: 30 },
  'h2': { sm: 22, md: 24 },
  'h3': { sm: 18, md: 22 },
  'h4': { sm: 16, md: 18 },
  'h5': { sm: 14, md: 15 },
  'label-1': { sm: 15, md: 16 },
  'label-2': { sm: 14, md: 15 },
  'label-3': { sm: 15 },
  'body': { sm: 16 },
  'lead-text': { sm: 18 },
  'help-text': { sm: 14 },
};

module.exports = {
  systemUIFontStack,
  fontSize,
  typeScale,
};
