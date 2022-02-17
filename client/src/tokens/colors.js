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
      js: 'warning-50',
      css: 'warning-50',
      bgUtility: 'bg-warning-50',
      textUtility: 'text-warning-50',
      usage: '',
      contrastText: '',
    },
    200: {
      hex: '#E9B04D',
      js: 'warning-200',
      css: 'warning-200',
      bgUtility: 'bg-warning-200',
      textUtility: 'text-warning-200',
      usage: '',
      contrastText: '',
    },
    DEFAULT: {
      hex: '#E9B04D',
      js: 'warning',
      css: 'warning',
      bgUtility: 'bg-warning',
      textUtility: 'text-warning',
      usage: '',
      contrastText: '',
    },
  },
  info: {
    50: {
      hex: '#EAFAFF',
      js: 'info-50',
      css: 'info-50',
      bgUtility: 'bg-info-50',
      textUtility: 'text-info-50',
      usage: '',
      contrastText: '',
    },
    100: {
      hex: '#5BC0DE',
      js: 'info-100',
      css: 'info-100',
      bgUtility: 'bg-info-100',
      textUtility: 'text-info-100',
      usage: '',
      contrastText: '',
    },
  },
  positive: {
    DEFAULT: {
      hex: '#008758',
      js: 'positive',
      css: 'positive',
      bgUtility: 'bg-positive',
      textUtility: 'text-positive',
      usage: '',
      contrastText: '',
    },
    50: {
      hex: '#E0FBF4',
      js: 'positive-50',
      css: 'positive-50',
      bgUtility: 'bg-positive-50',
      textUtility: 'text-positive-50',
      usage: '',
      contrastText: '',
    },
    100: {
      hex: '#008758',
      js: 'positive-100',
      css: 'positive-100',
      bgUtility: 'bg-positive-100',
      textUtility: 'text-positive-100',
      usage: '',
      contrastText: '',
    },
  },
  grey: {
    50: {
      hex: '#F9F9F9',
      js: 'grey-50',
      css: 'grey-50',
      bgUtility: 'bg-grey-50',
      textUtility: 'text-grey-50',
      usage: '',
      contrastText: '',
    },
    100: {
      hex: '#E0E0E0',
      js: 'grey-100',
      css: 'grey-100',
      bgUtility: 'bg-grey-100',
      textUtility: 'text-grey-100',
      usage: '',
      contrastText: '',
    },
    200: {
      hex: '#929292',
      js: 'grey-200',
      css: 'grey-200',
      bgUtility: 'bg-grey-200',
      textUtility: 'text-grey-200',
      usage: '',
      contrastText: '',
    },
    400: {
      hex: '#5C5C5C',
      js: 'grey-400',
      css: 'grey-400',
      bgUtility: 'bg-grey-400',
      textUtility: 'text-grey-400',
      usage: '',
      contrastText: '',
    },
    600: {
      hex: '#262626',
      js: 'grey-600',
      css: 'grey-600',
      bgUtility: 'bg-grey-600',
      textUtility: 'text-grey-600',
      usage: '',
      contrastText: '',
    },
    DEFAULT: {
      hex: '#262626',
      js: 'grey',
      css: 'grey',
      bgUtility: 'bg-grey',
      textUtility: 'text-grey',
      usage: '',
      contrastText: '',
    },
  },
  critical: {
    50: {
      hex: '#FFDDDF',
      js: 'critical-50',
      css: 'critical-50',
      bgUtility: 'bg-critical-50',
      textUtility: 'text-critical-50',
      usage: '',
      contrastText: '',
    },
    100: {
      hex: '#FD5765',
      js: 'critical-100',
      css: 'critical-100',
      bgUtility: 'bg-critical-100',
      textUtility: 'text-critical-100',
      usage: '',
      contrastText: '',
    },
    200: {
      hex: '#EB0316',
      js: 'critical-200',
      css: 'critical-200',
      bgUtility: 'bg-critical-200',
      textUtility: 'text-critical-200',
      usage: '',
      contrastText: '',
    },
    DEFAULT: {
      hex: '#EB0316',
      js: 'critical',
      css: 'critical',
      bgUtility: 'bg-critical',
      textUtility: 'text-critical',
      usage: '',
      contrastText: '',
    },
  },
  teal: {
    50: {
      hex: '#F2FCFC',
      js: 'teal-50',
      css: 'teal-50',
      bgUtility: 'bg-teal-50',
      textUtility: 'text-teal-50',
      usage: '',
      contrastText: '',
    },
    100: {
      hex: '#00B0B1',
      js: 'teal-100',
      css: 'teal-100',
      bgUtility: 'bg-teal-100',
      textUtility: 'text-teal-100',
      usage: '',
      contrastText: '',
    },
    200: {
      hex: '#007D7E',
      js: 'teal-200',
      css: 'teal-200',
      bgUtility: 'bg-teal-200',
      textUtility: 'text-teal-200',
      usage: '',
      contrastText: '',
    },
    400: {
      hex: '#005B5E',
      js: 'teal-400',
      css: 'teal-400',
      bgUtility: 'bg-teal-400',
      textUtility: 'text-teal-400',
      usage: '',
      contrastText: '',
    },
    DEFAULT: {
      hex: '#005B5E',
      js: 'teal',
      css: 'teal',
      bgUtility: 'bg-teal',
      textUtility: 'text-teal',
      usage: '',
      contrastText: '',
    },
  },
  primary: {
    DEFAULT: {
      hex: '#2E1F5E',
      js: 'primary',
      css: 'primary',
      bgUtility: 'bg-primary',
      textUtility: 'text-primary',
      usage: '',
      contrastText: '',
    },
  },
  white: {
    DEFAULT: {
      hex: '#FFFFFF',
      js: 'white',
      css: 'white',
      bgUtility: 'bg-white',
      textUtility: 'text-white',
      usage: '',
      contrastText: '',
    },
  },
};

module.exports = {
  ...colors,
};
