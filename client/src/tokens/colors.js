/** @typedef {{
    hex: string;
    bgUtility: string;
    textUtility: string;
    usage: string;
    contrastText: string;
}} Shade */

/** @typedef {{
    [jsName: string]: Shade;
}} Hues */

/** @typedef {{
    [jsName: string]: Hues;
}} Colors */

/** @type {Colors} */
const colors = {
  black: {
    DEFAULT: {
      hex: '#000000',
      bgUtility: 'w-bg-black',
      textUtility: 'w-text-black',
      usage: 'Shadows only',
      contrastText: 'white',
    },
  },
  grey: {
    600: {
      hex: '#262626',
      bgUtility: 'w-bg-grey-600',
      textUtility: 'w-text-grey-600',
      usage: 'Body copy, user content',
      contrastText: 'white',
    },
    400: {
      hex: '#5C5C5C',
      bgUtility: 'w-bg-grey-400',
      textUtility: 'w-text-grey-400',
      usage: 'Help text, placeholders, meta text, neutral state indicators',
      contrastText: 'white',
    },
    200: {
      hex: '#929292',
      bgUtility: 'w-bg-grey-200',
      textUtility: 'w-text-grey-200',
      usage: 'Dividers, button borders',
      contrastText: 'primary',
    },
    100: {
      hex: '#E0E0E0',
      bgUtility: 'w-bg-grey-100',
      textUtility: 'w-text-grey-100',
      usage: 'Dividers, field borders, panel borders',
      contrastText: 'primary',
    },
    50: {
      hex: '#F6F6F8',
      bgUtility: 'w-bg-grey-50',
      textUtility: 'w-text-grey-50',
      usage: 'Background for panels, row highlights',
      contrastText: 'primary',
    },
  },
  white: {
    DEFAULT: {
      hex: '#FFFFFF',
      bgUtility: 'w-bg-white',
      textUtility: 'w-text-white',
      usage: 'Page backgrounds, Panels, Button text',
      contrastText: 'primary',
    },
  },
  teal: {
    600: {
      hex: '#004345',
      bgUtility: 'w-bg-teal-600',
      textUtility: 'w-text-teal-600',
      usage: 'Hover states for two-tone buttons',
      contrastText: 'white',
    },
    400: {
      hex: '#005B5E',
      bgUtility: 'w-bg-teal-400',
      textUtility: 'w-text-teal-400',
      usage: 'Two-tone buttons, hover states',
      contrastText: 'white',
    },
    200: {
      hex: '#007D7E',
      bgUtility: 'w-bg-teal-200',
      textUtility: 'w-text-teal-200',
      usage: 'Primary buttons, action links',
      contrastText: 'white',
    },
    100: {
      hex: '#00B0B1',
      bgUtility: 'w-bg-teal-100',
      textUtility: 'w-text-teal-100',
      usage: 'UI element highlights',
      contrastText: 'white',
    },
    50: {
      hex: '#F2FCFC',
      bgUtility: 'w-bg-teal-50',
      textUtility: 'w-text-teal-50',
      usage: 'Button backgrounds, highlighted fields background',
      contrastText: 'teal-200',
    },
  },
  primary: {
    DEFAULT: {
      hex: '#2E1F5E',
      bgUtility: 'w-bg-primary',
      textUtility: 'w-text-primary',
      usage: 'Wagtail branding, Panels, Headings, Buttons, Labels',
      contrastText: 'white',
    },
    200: {
      hex: '#261A4E',
      bgUtility: 'w-bg-primary-200',
      textUtility: 'w-text-primary-200',
      usage:
        'Accent for elements used in conjunction with primary colour in sidebar',
      contrastText: 'white',
    },
  },
  info: {
    100: {
      hex: '#1F7E9A',
      bgUtility: 'w-bg-info-100',
      textUtility: 'w-text-info-100',
      usage: 'Background and icons for information messages',
      contrastText: 'white',
    },
    50: {
      hex: '#E2F5FC',
      bgUtility: 'w-bg-info-50',
      textUtility: 'w-text-info-50',
      usage: 'Background only, for information messages',
      contrastText: 'primary',
    },
  },
  positive: {
    100: {
      hex: '#1B8666',
      bgUtility: 'w-bg-positive-100',
      textUtility: 'w-text-positive-100',
      usage: 'Positive states',
      contrastText: 'white',
    },
    50: {
      hex: '#E0FBF4',
      bgUtility: 'w-bg-positive-50',
      textUtility: 'w-text-positive-50',
      usage: 'Background only, for positive states',
      contrastText: 'primary',
    },
  },
  warning: {
    100: {
      hex: '#FAA500',
      bgUtility: 'w-bg-warning-100',
      textUtility: 'w-text-warning-100',
      usage: 'Background and icons for potentially dangerous states',
      contrastText: 'primary',
    },
    50: {
      hex: '#FAECD5',
      bgUtility: 'w-bg-warning-50',
      textUtility: 'w-text-warning-50',
      usage: 'Background only, for potentially dangerous states',
      contrastText: 'primary',
    },
  },
  critical: {
    200: {
      hex: '#CD4444',
      bgUtility: 'w-bg-critical-200',
      textUtility: 'w-text-critical-200',
      usage: 'Dangerous actions or states (over light background), errors',
      contrastText: 'white',
    },
    100: {
      hex: '#FD5765',
      bgUtility: 'w-bg-critical-100',
      textUtility: 'w-text-critical-100',
      usage: 'Dangerous actions or states (over dark background)',
      contrastText: 'primary',
    },
    50: {
      hex: '#FDE9E9',
      bgUtility: 'w-bg-critical-50',
      textUtility: 'w-text-critical-50',
      usage: 'Background only, for dangerous states',
      contrastText: 'primary',
    },
  },
};

module.exports = colors;
