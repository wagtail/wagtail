/** @typedef {{
 sm: string;
 md: string;
 lg: string;
 xl: string;
}} Breakpoints */

/** @type {Breakpoints} */
const breakpoints = {
  sm: '30em', // 480px
  md: '48em', // 768px
  lg: '61em', // 976px
  xl: '90em', // 1440px
};

module.exports = {
  breakpoints,
};
