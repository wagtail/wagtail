const borderRadius = {
  none: '0',
  sm: '0.1875rem', // 3px
  DEFAULT: '0.3125rem', // 5px
  md: '0.625rem', // 10px
  xl: '1.5rem', // 24px
  full: '100%',
};

// If adding new values, use numerical naming.
const borderWidth = {
  DEFAULT: '0.0625rem', // 1px
  0: '0',
  2: '0.125rem', // 2px
  5: '0.3125rem', // 5px
};

// If adding new values, use T-shirt sizing naming.
const boxShadow = {
  DEFAULT: '5px 5px 20px rgba(0, 0, 0, 0.05)',
  md: '5px 5px 30px var(--w-color-box-shadow-md)',
};

module.exports = {
  borderRadius,
  borderWidth,
  boxShadow,
};
