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
      js: 'w-warning-50',
      css: 'w-warning-50',
      bgUtility: 'w-bg-warning-50',
      textUtility: 'w-text-warning-50',
      usage: '',
      contrastText: '',
    },
    200: {
      hex: '#E9B04D',
      js: 'w-warning-200',
      css: 'w-warning-200',
      bgUtility: 'w-bg-warning-200',
      textUtility: 'w-text-warning-200',
      usage: '',
      contrastText: '',
    },
    DEFAULT: {
      hex: '#E9B04D',
      js: 'w-warning',
      css: 'w-warning',
      bgUtility: 'w-bg-warning',
      textUtility: 'w-text-warning',
      usage: '',
      contrastText: '',
    },
  },
  info: {
    50: {
      hex: '#EAFAFF',
      js: 'w-info-50',
      css: 'w-info-50',
      bgUtility: 'w-bg-info-50',
      textUtility: 'w-text-info-50',
      usage: '',
      contrastText: '',
    },
    100: {
      hex: '#5BC0DE',
      js: 'w-info-100',
      css: 'w-info-100',
      bgUtility: 'w-bg-info-100',
      textUtility: 'w-text-info-100',
      usage: '',
      contrastText: '',
    },
  },
  positive: {
    DEFAULT: {
      hex: '#008758',
      js: 'w-positive',
      css: 'w-positive',
      bgUtility: 'w-bg-positive',
      textUtility: 'w-text-positive',
      usage: '',
      contrastText: '',
    },
    50: {
      hex: '#E0FBF4',
      js: 'w-positive-50',
      css: 'w-positive-50',
      bgUtility: 'w-bg-positive-50',
      textUtility: 'w-text-positive-50',
      usage: '',
      contrastText: '',
    },
    100: {
      hex: '#008758',
      js: 'w-positive-100',
      css: 'w-positive-100',
      bgUtility: 'w-bg-positive-100',
      textUtility: 'w-text-positive-100',
      usage: '',
      contrastText: '',
    },
  },
  grey: {
    50: {
      hex: '#F9F9F9',
      js: 'w-grey-50',
      css: 'w-grey-50',
      bgUtility: 'w-bg-grey-50',
      textUtility: 'w-text-grey-50',
      usage: '',
      contrastText: '',
    },
    100: {
      hex: '#E0E0E0',
      js: 'w-grey-100',
      css: 'w-grey-100',
      bgUtility: 'w-bg-grey-100',
      textUtility: 'w-text-grey-100',
      usage: '',
      contrastText: '',
    },
    200: {
      hex: '#929292',
      js: 'w-grey-200',
      css: 'w-grey-200',
      bgUtility: 'w-bg-grey-200',
      textUtility: 'w-text-grey-200',
      usage: '',
      contrastText: '',
    },
    400: {
      hex: '#5C5C5C',
      js: 'w-grey-400',
      css: 'w-grey-400',
      bgUtility: 'w-bg-grey-400',
      textUtility: 'w-text-grey-400',
      usage: '',
      contrastText: '',
    },
    600: {
      hex: '#262626',
      js: 'w-grey-600',
      css: 'w-grey-600',
      bgUtility: 'w-bg-grey-600',
      textUtility: 'w-text-grey-600',
      usage: '',
      contrastText: '',
    },
    DEFAULT: {
      hex: '#262626',
      js: 'w-grey',
      css: 'w-grey',
      bgUtility: 'w-bg-grey',
      textUtility: 'w-text-grey',
      usage: '',
      contrastText: '',
    },
  },
  critical: {
    50: {
      hex: '#FFDDDF',
      js: 'w-critical-50',
      css: 'w-critical-50',
      bgUtility: 'w-bg-critical-50',
      textUtility: 'w-text-critical-50',
      usage: '',
      contrastText: '',
    },
    100: {
      hex: '#FD5765',
      js: 'w-critical-100',
      css: 'w-critical-100',
      bgUtility: 'w-bg-critical-100',
      textUtility: 'w-text-critical-100',
      usage: '',
      contrastText: '',
    },
    200: {
      hex: '#EB0316',
      js: 'w-critical-200',
      css: 'w-critical-200',
      bgUtility: 'w-bg-critical-200',
      textUtility: 'w-text-critical-200',
      usage: '',
      contrastText: '',
    },
    DEFAULT: {
      hex: '#EB0316',
      js: 'w-critical',
      css: 'w-critical',
      bgUtility: 'w-bg-critical',
      textUtility: 'w-text-critical',
      usage: '',
      contrastText: '',
    },
  },
  teal: {
    50: {
      hex: '#F2FCFC',
      js: 'w-teal-50',
      css: 'w-teal-50',
      bgUtility: 'w-bg-teal-50',
      textUtility: 'w-text-teal-50',
      usage: '',
      contrastText: '',
    },
    100: {
      hex: '#00B0B1',
      js: 'w-teal-100',
      css: 'w-teal-100',
      bgUtility: 'w-bg-teal-100',
      textUtility: 'w-text-teal-100',
      usage: '',
      contrastText: '',
    },
    200: {
      hex: '#007D7E',
      js: 'w-teal-200',
      css: 'w-teal-200',
      bgUtility: 'w-bg-teal-200',
      textUtility: 'w-text-teal-200',
      usage: '',
      contrastText: '',
    },
    400: {
      hex: '#005B5E',
      js: 'w-teal-400',
      css: 'w-teal-400',
      bgUtility: 'w-bg-teal-400',
      textUtility: 'w-text-teal-400',
      usage: '',
      contrastText: '',
    },
    DEFAULT: {
      hex: '#005B5E',
      js: 'w-teal',
      css: 'w-teal',
      bgUtility: 'w-bg-teal',
      textUtility: 'w-text-teal',
      usage: '',
      contrastText: '',
    },
  },
  primary: {
    DEFAULT: {
      hex: '#2E1F5E',
      js: 'w-primary',
      css: 'w-primary',
      bgUtility: 'w-bg-primary',
      textUtility: 'w-text-primary',
      usage: '',
      contrastText: '',
    },
  },
  white: {
    DEFAULT: {
      hex: '#FFFFFF',
      js: 'w-white',
      css: 'w-white',
      bgUtility: 'w-bg-white',
      textUtility: 'w-text-white',
      usage: '',
      contrastText: '',
    },
  },
};

module.exports = {
  ...colors,
};
