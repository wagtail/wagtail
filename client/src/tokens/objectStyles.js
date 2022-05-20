const borderRadius = {
  none: '0',
  sm: '0.1875rem', // 3px
  DEFAULT: '0.3125rem', // 5px
  md: '0.625rem', // 10px
  full: '100%',
};

// If adding new values, use numerical naming.
const borderWidth = {
  DEFAULT: '0.0625rem', // 1px
  0: '0',
  5: '0.3125rem',
};

// If adding new values, use T-shirt sizing naming.
const boxShadow = {
  DEFAULT: '5px 5px 20px rgba(0, 0, 0, 0.05)',
};

module.exports = {
  borderRadius,
  borderWidth,
  boxShadow,
};
