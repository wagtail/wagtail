/** @typedef {{
    hex: string;
    hsl: string;
    bgUtility: string;
    textUtility: string;
    cssVariable: string;
    usage: string;
    contrastText: string;
}} Shade */

/** @typedef {{
    [jsName: string | number]: Shade;
}} Hues */

/** @typedef {{
    [jsName: string]: Hues;
}} Colors */

/** @type {Colors} */
const staticColors = {
  black: {
    DEFAULT: {
      hex: '#000000',
      hsl: 'hsl(0 0% 0%)',
      bgUtility: 'w-bg-black',
      textUtility: 'w-text-black',
      cssVariable: '--w-color-black',
      usage: 'Shadows only',
      contrastText: 'white',
    },
  },
  grey: {
    800: {
      hex: '#1D1D1D',
      hsl: 'hsl(0 0% 11.4%)',
      bgUtility: 'w-bg-grey-800',
      textUtility: 'w-text-grey-800',
      cssVariable: '--w-color-grey-800',
      usage: 'Backgrounds for panels in dark theme',
      contrastText: 'white',
    },
    700: {
      hex: '#222222',
      hsl: 'hsl(0 0% 13.3%)',
      bgUtility: 'w-bg-grey-700',
      textUtility: 'w-text-grey-700',
      cssVariable: '--w-color-grey-700',
      usage: 'Backgrounds for panels in dark theme',
      contrastText: 'white',
    },
    600: {
      hex: '#262626',
      hsl: 'hsl(0 0% 14.9%)',
      bgUtility: 'w-bg-grey-600',
      textUtility: 'w-text-grey-600',
      cssVariable: '--w-color-grey-600',
      usage: 'Body copy, user content',
      contrastText: 'white',
    },
    500: {
      hex: '#333333',
      hsl: 'hsl(0 0% 20%)',
      bgUtility: 'w-bg-grey-500',
      textUtility: 'w-text-grey-500',
      cssVariable: '--w-color-grey-500',
      usage: 'Panels, dividers in dark mode',
      contrastText: 'white',
    },
    400: {
      hex: '#5C5C5C',
      hsl: 'hsl(0 0% 36.1%)',
      bgUtility: 'w-bg-grey-400',
      textUtility: 'w-text-grey-400',
      cssVariable: '--w-color-grey-400',
      usage: 'Help text, placeholders, meta text, neutral state indicators',
      contrastText: 'white',
    },
    200: {
      hex: '#929292',
      hsl: 'hsl(0 0% 57.3%)',
      bgUtility: 'w-bg-grey-200',
      textUtility: 'w-text-grey-200',
      cssVariable: '--w-color-grey-200',
      usage: 'Dividers, button borders',
      contrastText: 'primary',
    },
    150: {
      hex: '#C8C8C8',
      hsl: 'hsl(0 0% 78.4%)',
      bgUtility: 'w-bg-grey-150',
      textUtility: 'w-text-grey-150',
      cssVariable: '--w-color-grey-150',
      usage: 'Field borders',
      contrastText: 'primary',
    },
    100: {
      hex: '#E0E0E0',
      hsl: 'hsl(0 0% 87.8%)',
      bgUtility: 'w-bg-grey-100',
      textUtility: 'w-text-grey-100',
      cssVariable: '--w-color-grey-100',
      usage: 'Dividers, panel borders',
      contrastText: 'primary',
    },
    50: {
      hex: '#F6F6F8',
      hsl: 'hsl(240 12.5% 96.9%)',
      bgUtility: 'w-bg-grey-50',
      textUtility: 'w-text-grey-50',
      cssVariable: '--w-color-grey-50',
      usage: 'Background for panels, row highlights',
      contrastText: 'primary',
    },
  },
  white: {
    DEFAULT: {
      hex: '#FFFFFF',
      hsl: 'hsl(0 0% 100%)',
      bgUtility: 'w-bg-white',
      textUtility: 'w-text-white',
      cssVariable: '--w-color-white',
      usage: 'Page backgrounds, Panels, Button text',
      contrastText: 'primary',
    },
  },
  primary: {
    DEFAULT: {
      hex: '#2E1F5E',
      hsl: 'hsl(254.3 50.4% 24.5%)',
      bgUtility: 'w-bg-primary',
      textUtility: 'w-text-primary',
      cssVariable: '--w-color-primary',
      usage: 'Wagtail branding, Panels, Headings, Buttons, Labels',
      contrastText: 'white',
    },
    200: {
      hex: '#261A4E',
      hsl: 'hsl(253.8 50% 20.4%)',
      bgUtility: 'w-bg-primary-200',
      textUtility: 'w-text-primary-200',
      cssVariable: '--w-color-primary-200',
      usage:
        'Accent for elements used in conjunction with primary colour in sidebar',
      contrastText: 'white',
    },
  },
  secondary: {
    600: {
      hex: '#004345',
      hsl: 'hsl(181.7 100% 13.5%)',
      bgUtility: 'w-bg-secondary-600',
      textUtility: 'w-text-secondary-600',
      cssVariable: '--w-color-secondary-600',
      usage: 'Hover states for two-tone buttons',
      contrastText: 'white',
    },
    400: {
      hex: '#005B5E',
      hsl: 'hsl(181.9 100% 18.4%)',
      bgUtility: 'w-bg-secondary-400',
      textUtility: 'w-text-secondary-400',
      cssVariable: '--w-color-secondary-400',
      usage: 'Two-tone buttons, hover states',
      contrastText: 'white',
    },
    DEFAULT: {
      hex: '#007D7E',
      hsl: 'hsl(180.5 100% 24.7%)',
      bgUtility: 'w-bg-secondary',
      textUtility: 'w-text-secondary',
      cssVariable: '--w-color-secondary',
      usage: 'Primary buttons, action links',
      contrastText: 'white',
    },
    100: {
      hex: '#00B0B1',
      hsl: 'hsl(180.3 100% 34.7%)',
      bgUtility: 'w-bg-secondary-100',
      textUtility: 'w-text-secondary-100',
      cssVariable: '--w-color-secondary-100',
      usage: 'UI element highlights over dark backgrounds',
      contrastText: 'white',
    },
    75: {
      hex: '#80D7D8',
      hsl: 'hsl(180.7 53% 67.5%)',
      bgUtility: 'w-bg-secondary-75',
      textUtility: 'w-text-secondary-75',
      cssVariable: '--w-color-secondary-75',
      usage: 'UI element highlights over dark text',
      contrastText: 'primary',
    },
    50: {
      hex: '#F2FCFC',
      hsl: 'hsl(180 62.5% 96.9%)',
      bgUtility: 'w-bg-secondary-50',
      textUtility: 'w-text-secondary-50',
      cssVariable: '--w-color-secondary-50',
      usage: 'Button backgrounds, highlighted fields background',
      contrastText: 'secondary',
    },
  },
  info: {
    125: {
      hex: '#186076',
      hsl: 'hsl(194.0, 66.2%, 27.8%)',
      bgUtility: 'w-bg-info-125',
      textUtility: 'w-text-info-125',
      cssVariable: '--w-color-info-125',
      usage: 'Hover background only, for information messages',
      contrastText: 'white',
    },
    100: {
      hex: '#1D7792',
      hsl: 'hsl(193.9 66.9% 34.3%)',
      bgUtility: 'w-bg-info-100',
      textUtility: 'w-text-info-100',
      cssVariable: '--w-color-info-100',
      usage: 'Background and icons for information messages',
      contrastText: 'white',
    },
    75: {
      hex: '#80B6C7',
      hsl: 'hsl(194.4, 38.8%, 64.1%)',
      bgUtility: 'w-bg-info-75',
      textUtility: 'w-text-info-75',
      cssVariable: '--w-color-info-75',
      usage: 'Info text in the dark theme',
      contrastText: 'primary',
    },
    50: {
      hex: '#E2F5FC',
      hsl: 'hsl(196.2 81.3% 93.7%)',
      bgUtility: 'w-bg-info-50',
      textUtility: 'w-text-info-50',
      cssVariable: '--w-color-info-50',
      usage: 'Background only, for information messages',
      contrastText: 'primary',
    },
  },
  positive: {
    100: {
      hex: '#1B8666',
      hsl: 'hsl(162.1 66.5% 31.6%)',
      bgUtility: 'w-bg-positive-100',
      textUtility: 'w-text-positive-100',
      cssVariable: '--w-color-positive-100',
      usage: 'Positive states',
      contrastText: 'white',
    },
    50: {
      hex: '#E0FBF4',
      hsl: 'hsl(164.4 77.1% 93.1%)',
      bgUtility: 'w-bg-positive-50',
      textUtility: 'w-text-positive-50',
      cssVariable: '--w-color-positive-50',
      usage: 'Background only, for positive states',
      contrastText: 'primary',
    },
  },
  warning: {
    100: {
      hex: '#FAA500',
      hsl: 'hsl(39.6 100% 49%)',
      bgUtility: 'w-bg-warning-100',
      textUtility: 'w-text-warning-100',
      cssVariable: '--w-color-warning-100',
      usage: 'Background and icons for potentially dangerous states',
      contrastText: 'primary',
    },
    75: {
      hex: '#FDD074',
      hsl: 'hsl(40.3, 97.2%, 72.4%)',
      bgUtility: 'w-bg-warning-75',
      textUtility: 'w-text-warning-75',
      cssVariable: '--w-color-warning-75',
      usage:
        'Background only, for potentially dangerous states, in enhanced-contrast theme',
      contrastText: 'primary',
    },
    50: {
      hex: '#FFF5D8',
      hsl: 'hsl(37.3 78.7% 90.8%)',
      bgUtility: 'w-bg-warning-50',
      textUtility: 'w-text-warning-50',
      cssVariable: '--w-color-warning-50',
      usage: 'Background only, for potentially dangerous states',
      contrastText: 'primary',
    },
  },
  critical: {
    200: {
      hex: '#CA3B3B',
      hsl: 'hsl(0 57.4% 51.2%)',
      bgUtility: 'w-bg-critical-200',
      textUtility: 'w-text-critical-200',
      cssVariable: '--w-color-critical-200',
      usage: 'Dangerous actions or states (over light background), errors',
      contrastText: 'white',
    },
    100: {
      hex: '#FD5765',
      hsl: 'hsl(354.9 97.6% 66.7%)',
      bgUtility: 'w-bg-critical-100',
      textUtility: 'w-text-critical-100',
      cssVariable: '--w-color-critical-100',
      usage: 'Dangerous actions or states (over dark background)',
      contrastText: 'primary',
    },
    50: {
      hex: '#FEF0F0',
      hsl: 'hsl(0 87.5% 96.9%)',
      bgUtility: 'w-bg-critical-50',
      textUtility: 'w-text-critical-50',
      cssVariable: '--w-color-critical-50',
      usage: 'Background only, for dangerous states',
      contrastText: 'primary',
    },
  },
};

const transparencies = {
  '--w-color-white-10': 'rgba(255, 255, 255, 0.10)',
  '--w-color-white-15': 'rgba(255, 255, 255, 0.15)',
  '--w-color-white-50': 'rgba(255, 255, 255, 0.50)',
  '--w-color-white-80': 'rgba(255, 255, 255, 0.80)',
  '--w-color-black-5': 'rgba(0, 0, 0, 0.05)',
  '--w-color-black-10': 'rgba(0, 0, 0, 0.10)',
  '--w-color-black-20': 'rgba(0, 0, 0, 0.20)',
  '--w-color-black-25': 'rgba(0, 0, 0, 0.25)',
  '--w-color-black-35': 'rgba(0, 0, 0, 0.35)',
  '--w-color-black-50': 'rgba(0, 0, 0, 0.50)',
};

module.exports = {
  staticColors,
  transparencies,
};
