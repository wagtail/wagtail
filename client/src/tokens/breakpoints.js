/** @typedef {{
 sm: string;
 md: string;
 lg: string;
 xl: string;
}} Breakpoints */

/** @type {Breakpoints} */
const breakpoints = {
  sm: '50em', // 800px
  md: '56.25em', // 900px
  lg: '75em', // 1200px
  xl: '100em', // 1600px
};

module.exports = {
  breakpoints,
};
