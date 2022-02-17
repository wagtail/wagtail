/** @typedef {string} ColorHex */
/** @typedef {string} ColorJS */
/** @typedef {string} ColorCSS */

/** @typedef {{
    hex: ColorHex;
    js: ColorJS;
    css: ColorCSS;
    bgUtility: ColorCSS;
    textUtility: ColorCSS;
    usage: string;
    contrastText: keyof typeof allColors;
}} Shade */

/** @typedef {{
    [jsName: string]: Shade;
}} Color */

/** @type {Color} */
const colors = {
  warning: {
    50: {
      hex: '#faecd5',
      js: 'wt-warning-50',
      css: 'wt-warning-50',
      bgUtility: 'wt-bg-warning-50',
      textUtility: 'wt-text-warning-50',
      usage: '',
      contrastText: '',
    },
    200: {
      hex: '#E9B04D',
      js: 'wt-warning-200',
      css: 'wt-warning-200',
      bgUtility: 'wt-bg-warning-200',
      textUtility: 'wt-text-warning-200',
      usage: '',
      contrastText: '',
    },
    DEFAULT: {
      hex: '#E9B04D',
      js: 'wt-warning',
      css: 'wt-warning',
      bgUtility: 'wt-bg-warning',
      textUtility: 'wt-text-warning',
      usage: '',
      contrastText: '',
    },
  },
  info: {
    50: {
      hex: '#EAFAFF',
      js: 'wt-info-50',
      css: 'wt-info-50',
      bgUtility: 'wt-bg-info-50',
      textUtility: 'wt-text-info-50',
      usage: '',
      contrastText: '',
    },
    100: {
      hex: '#5BC0DE',
      js: 'wt-info-100',
      css: 'wt-info-100',
      bgUtility: 'wt-bg-info-100',
      textUtility: 'wt-text-info-100',
      usage: '',
      contrastText: '',
    },
  },
  positive: {
    DEFAULT: {
      hex: '#008758',
      js: 'wt-positive',
      css: 'wt-positive',
      bgUtility: 'wt-bg-positive',
      textUtility: 'wt-text-positive',
      usage: '',
      contrastText: '',
    },
    50: {
      hex: '#E0FBF4',
      js: 'wt-positive-50',
      css: 'wt-positive-50',
      bgUtility: 'wt-bg-positive-50',
      textUtility: 'wt-text-positive-50',
      usage: '',
      contrastText: '',
    },
    100: {
      hex: '#008758',
      js: 'wt-positive-100',
      css: 'wt-positive-100',
      bgUtility: 'wt-bg-positive-100',
      textUtility: 'wt-text-positive-100',
      usage: '',
      contrastText: '',
    },
  },
  grey: {
    50: {
      hex: '#F9F9F9',
      js: 'wt-grey-50',
      css: 'wt-grey-50',
      bgUtility: 'wt-bg-grey-50',
      textUtility: 'wt-text-grey-50',
      usage: '',
      contrastText: '',
    },
    100: {
      hex: '#E0E0E0',
      js: 'wt-grey-100',
      css: 'wt-grey-100',
      bgUtility: 'wt-bg-grey-100',
      textUtility: 'wt-text-grey-100',
      usage: '',
      contrastText: '',
    },
    200: {
      hex: '#929292',
      js: 'wt-grey-200',
      css: 'wt-grey-200',
      bgUtility: 'wt-bg-grey-200',
      textUtility: 'wt-text-grey-200',
      usage: '',
      contrastText: '',
    },
    400: {
      hex: '#5C5C5C',
      js: 'wt-grey-400',
      css: 'wt-grey-400',
      bgUtility: 'wt-bg-grey-400',
      textUtility: 'wt-text-grey-400',
      usage: '',
      contrastText: '',
    },
    600: {
      hex: '#262626',
      js: 'wt-grey-600',
      css: 'wt-grey-600',
      bgUtility: 'wt-bg-grey-600',
      textUtility: 'wt-text-grey-600',
      usage: '',
      contrastText: '',
    },
    DEFAULT: {
      hex: '#262626',
      js: 'wt-grey',
      css: 'wt-grey',
      bgUtility: 'wt-bg-grey',
      textUtility: 'wt-text-grey',
      usage: '',
      contrastText: '',
    },
  },
  critical: {
    50: {
      hex: '#FFDDDF',
      js: 'wt-critical-50',
      css: 'wt-critical-50',
      bgUtility: 'wt-bg-critical-50',
      textUtility: 'wt-text-critical-50',
      usage: '',
      contrastText: '',
    },
    100: {
      hex: '#FD5765',
      js: 'wt-critical-100',
      css: 'wt-critical-100',
      bgUtility: 'wt-bg-critical-100',
      textUtility: 'wt-text-critical-100',
      usage: '',
      contrastText: '',
    },
    200: {
      hex: '#EB0316',
      js: 'wt-critical-200',
      css: 'wt-critical-200',
      bgUtility: 'wt-bg-critical-200',
      textUtility: 'wt-text-critical-200',
      usage: '',
      contrastText: '',
    },
    DEFAULT: {
      hex: '#EB0316',
      js: 'wt-critical',
      css: 'wt-critical',
      bgUtility: 'wt-bg-critical',
      textUtility: 'wt-text-critical',
      usage: '',
      contrastText: '',
    },
  },
  teal: {
    50: {
      hex: '#F2FCFC',
      js: 'wt-teal-50',
      css: 'wt-teal-50',
      bgUtility: 'wt-bg-teal-50',
      textUtility: 'wt-text-teal-50',
      usage: '',
      contrastText: '',
    },
    100: {
      hex: '#00B0B1',
      js: 'wt-teal-100',
      css: 'wt-teal-100',
      bgUtility: 'wt-bg-teal-100',
      textUtility: 'wt-text-teal-100',
      usage: '',
      contrastText: '',
    },
    200: {
      hex: '#007D7E',
      js: 'wt-teal-200',
      css: 'wt-teal-200',
      bgUtility: 'wt-bg-teal-200',
      textUtility: 'wt-text-teal-200',
      usage: '',
      contrastText: '',
    },
    400: {
      hex: '#005B5E',
      js: 'wt-teal-400',
      css: 'wt-teal-400',
      bgUtility: 'wt-bg-teal-400',
      textUtility: 'wt-text-teal-400',
      usage: '',
      contrastText: '',
    },
    DEFAULT: {
      hex: '#005B5E',
      js: 'wt-teal',
      css: 'wt-teal',
      bgUtility: 'wt-bg-teal',
      textUtility: 'wt-text-teal',
      usage: '',
      contrastText: '',
    },
  },
  primary: {
    DEFAULT: {
      hex: '#2E1F5E',
      js: 'wt-primary',
      css: 'wt-primary',
      bgUtility: 'wt-bg-primary',
      textUtility: 'wt-text-primary',
      usage: '',
      contrastText: '',
    },
  },
  white: {
    DEFAULT: {
      hex: '#FFFFFF',
      js: 'wt-white',
      css: 'wt-white',
      bgUtility: 'wt-bg-white',
      textUtility: 'wt-text-white',
      usage: '',
      contrastText: '',
    },
  },
};

module.exports = {
  ...colors,
};
