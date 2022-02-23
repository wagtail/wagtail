/** @typedef {{
 sm: string;
 md: string;
 lg: string;
 xl: string;
}} Breakpoints */

/** @type {Breakpoints} */
const breakpoints = {
  xs: 0,
  sm: '50em',
  // 800px
  md: '56.25em',
  // 900px
  lg: '75em',
  // 1200px
  xl: '100em',
  // 1440px
};

module.exports = {
  breakpoints,
};
