/** @typedef {{
    value: svar(--w-color-trin)g;
    bgUtility: string;
    textUtility: string;
    cssVariable: string;
}} Token */

/** @typedef {{
    [token: string]: Token;
}} CategoryTokens */

/** @typedef {{
    label: string;
    tokens: CategoryTokens;
}} ThemeCategory */

// The focus outline color is defined without reusing a named color variable
// because it shouldn’t be reused for anything else in the UI.
const focusToken = {
  value: '#00A885',
  bgUtility: 'w-bg-focus',
  textUtility: 'w-text-focus',
  cssVariable: '--w-color-focus',
};

/** @type {ThemeCategory[]} */
const light = [
  {
    label: 'Surfaces - General',
    tokens: {
      'surface-page': {
        value: 'var(--w-color-white)',
        bgUtility: 'w-bg-surface-page',
        textUtility: 'w-text-surface-page',
        cssVariable: '--w-color-surface-page',
      },
      'surface-field': {
        value: 'var(--w-color-white)',
        bgUtility: 'w-bg-surface-field',
        textUtility: 'w-text-surface-field',
        cssVariable: '--w-color-surface-field',
      },
      'surface-field-inactive': {
        value: 'var(--w-color-grey-50)',
        bgUtility: 'w-bg-surface-field-inactive',
        textUtility: 'w-text-surface-field-inactive',
        cssVariable: '--w-color-surface-field-inactive',
      },
      'surface-header': {
        value: 'var(--w-color-grey-50)',
        bgUtility: 'w-bg-surface-header',
        textUtility: 'w-text-surface-header',
        cssVariable: '--w-color-surface-header',
      },
      'surface-menus': {
        value: 'var(--w-color-primary)',
        bgUtility: 'w-bg-surface-menus',
        textUtility: 'w-text-surface-menus',
        cssVariable: '--w-color-surface-menus',
      },
      'surface-menu-item-active': {
        value: 'var(--w-color-primary-200)',
        bgUtility: 'w-bg-surface-menu-item-active',
        textUtility: 'w-text-surface-menu-item-active',
        cssVariable: '--w-color-surface-menu-item-active',
      },
      'surface-tooltip': {
        value: 'var(--w-color-primary-200)',
        bgUtility: 'w-bg-surface-tooltip',
        textUtility: 'w-text-surface-tooltip',
        cssVariable: '--w-color-surface-tooltip',
      },
      'surface-button-default': {
        value: 'var(--w-color-secondary)',
        bgUtility: 'w-bg-surface-button-default',
        textUtility: 'w-text-surface-button-default',
        cssVariable: '--w-color-surface-button-default',
      },
      'surface-button-hover': {
        value: 'var(--w-color-secondary-400)',
        bgUtility: 'w-bg-surface-button-hover',
        textUtility: 'w-text-surface-button-hover',
        cssVariable: '--w-color-surface-button-hover',
      },
      'surface-button-inactive': {
        value: 'var(--w-color-grey-400)',
        bgUtility: 'w-bg-surface-button-inactive',
        textUtility: 'w-text-surface-button-inactive',
        cssVariable: '--w-color-surface-button-inactive',
      },
      'surface-button-outline-hover': {
        value: 'var(--w-color-secondary-50)',
        bgUtility: 'w-bg-surface-button-outline-hover',
        textUtility: 'w-text-surface-button-outline-hover',
        cssVariable: '--w-color-surface-button-outline-hover',
      },
    },
  },
  {
    label: 'Text',
    tokens: {
      'text-button': {
        value: 'var(--w-color-white)',
        bgUtility: 'w-bg-text-button',
        textUtility: 'w-text-text-button',
        cssVariable: '--w-color-text-button',
      },
      'text-label-menus-default': {
        value: 'var(--w-color-white-80)',
        bgUtility: 'w-bg-text-label-menus-default',
        textUtility: 'w-text-text-label-menus-default',
        cssVariable: '--w-color-text-label-menus-default',
      },
      'text-label-menus-active': {
        value: 'var(--w-color-white)',
        bgUtility: 'w-bg-text-label-menus-active',
        textUtility: 'w-text-text-label-menus-active',
        cssVariable: '--w-color-text-label-menus-active',
      },
      'text-label': {
        value: 'var(--w-color-primary)',
        bgUtility: 'w-bg-text-label',
        textUtility: 'w-text-text-label',
        cssVariable: '--w-color-text-label',
      },
      'text-context': {
        value: 'var(--w-color-grey-600)',
        bgUtility: 'w-bg-text-context',
        textUtility: 'w-text-text-context',
        cssVariable: '--w-color-text-context',
      },
      'text-meta': {
        value: 'var(--w-color-grey-400)',
        bgUtility: 'w-bg-text-meta',
        textUtility: 'w-text-text-meta',
        cssVariable: '--w-color-text-meta',
      },
      'text-placeholder': {
        value: 'var(--w-color-grey-400)',
        bgUtility: 'w-bg-text-placeholder',
        textUtility: 'w-text-text-placeholder',
        cssVariable: '--w-color-text-placeholder',
      },
      'text-link-default': {
        value: 'var(--w-color-secondary)',
        bgUtility: 'w-bg-text-link-default',
        textUtility: 'w-text-text-link-default',
        cssVariable: '--w-color-text-link-default',
      },
      'text-link-hover': {
        value: 'var(--w-color-secondary-400)',
        bgUtility: 'w-bg-text-link-hover',
        textUtility: 'w-text-text-link-hover',
        cssVariable: '--w-color-text-link-hover',
      },
      'text-button-outline-default': {
        value: 'var(--w-color-secondary)',
        bgUtility: 'w-bg-text-button-outline-default',
        textUtility: 'w-text-text-button-outline-default',
        cssVariable: '--w-color-text-button-outline-default',
      },
      'text-highlight': {
        value: 'var(--w-color-secondary-75)',
        bgUtility: 'w-bg-text-highlight',
        textUtility: 'w-text-text-highlight',
        cssVariable: '--w-color-text-highlight',
      },
      'text-error': {
        value: 'var(--w-color-critical-200)',
        bgUtility: 'w-bg-text-error',
        textUtility: 'w-text-text-error',
        cssVariable: '--w-color-text-error',
      },
    },
  },
  {
    label: 'Icons',
    tokens: {
      'icon-primary': {
        value: 'var(--w-color-primary)',
        bgUtility: 'w-bg-icon-primary',
        textUtility: 'w-text-icon-primary',
        cssVariable: '--w-color-icon-primary',
      },
      'icon-primary-hover': {
        value: 'var(--w-color-primary-200)',
        bgUtility: 'w-bg-icon-primary-hover',
        textUtility: 'w-text-icon-primary-hover',
        cssVariable: '--w-color-icon-primary-hover',
      },
      'icon-secondary': {
        value: 'var(--w-color-grey-400)',
        bgUtility: 'w-bg-icon-secondary',
        textUtility: 'w-text-icon-secondary',
        cssVariable: '--w-color-icon-secondary',
      },
      'icon-secondary-hover': {
        value: 'var(--w-color-primary-200)',
        bgUtility: 'w-bg-icon-secondary-hover',
        textUtility: 'w-text-icon-secondary-hover',
        cssVariable: '--w-color-icon-secondary-hover',
      },
    },
  },
  {
    label: 'Borders',
    tokens: {
      'border-furniture': {
        value: 'var(--w-color-grey-100)',
        bgUtility: 'w-bg-border-furniture',
        textUtility: 'w-text-border-furniture',
        cssVariable: '--w-color-border-furniture',
      },
      'border-button-small-outline-default': {
        value: 'var(--w-color-grey-150)',
        bgUtility: 'w-bg-border-button-small-outline-default',
        textUtility: 'w-text-border-button-small-outline-default',
        cssVariable: '--w-color-border-button-small-outline-default',
      },
      'border-field-default': {
        value: 'var(--w-color-grey-150)',
        bgUtility: 'w-bg-border-field-default',
        textUtility: 'w-text-border-field-default',
        cssVariable: '--w-color-border-field-default',
      },
      'border-field-inactive': {
        value: 'var(--w-color-grey-150)',
        bgUtility: 'w-bg-border-field-inactive',
        textUtility: 'w-text-border-field-inactive',
        cssVariable: '--w-color-border-field-inactive',
      },
      'border-field-hover': {
        value: 'var(--w-color-grey-200)',
        bgUtility: 'w-bg-border-field-hover',
        textUtility: 'w-text-border-field-hover',
        cssVariable: '--w-color-border-field-hover',
      },
      'border-button-outline-default': {
        value: 'var(--w-color-secondary)',
        bgUtility: 'w-bg-border-button-outline-default',
        textUtility: 'w-text-border-button-outline-default',
        cssVariable: '--w-color-border-button-outline-default',
      },
    },
  },
  {
    label: 'Misc',
    tokens: {
      focus: focusToken,
    },
  },
];

/** @type {ThemeCategory[]} */
const dark = [
  {
    label: 'Surfaces - General',
    tokens: {
      'surface-page': {
        value: 'var(--w-color-grey-600)',
        bgUtility: 'w-bg-surface-page',
        textUtility: 'w-text-surface-page',
        cssVariable: '--w-color-surface-page',
      },
      'surface-field': {
        value: 'var(--w-color-grey-600)',
        bgUtility: 'w-bg-surface-field',
        textUtility: 'w-text-surface-field',
        cssVariable: '--w-color-surface-field',
      },
      'surface-field-inactive': {
        value: 'var(--w-color-grey-500)',
        bgUtility: 'w-bg-surface-field-inactive',
        textUtility: 'w-text-surface-field-inactive',
        cssVariable: '--w-color-surface-field-inactive',
      },
      'surface-header': {
        value: 'var(--w-color-grey-600)',
        bgUtility: 'w-bg-surface-header',
        textUtility: 'w-text-surface-header',
        cssVariable: '--w-color-surface-header',
      },
      'surface-menus': {
        value: 'var(--w-color-grey-500)',
        bgUtility: 'w-bg-surface-menus',
        textUtility: 'w-text-surface-menus',
        cssVariable: '--w-color-surface-menus',
      },
      'surface-menu-item-active': {
        value: 'var(--w-color-grey-600)',
        bgUtility: 'w-bg-surface-menu-item-active',
        textUtility: 'w-text-surface-menu-item-active',
        cssVariable: '--w-color-surface-menu-item-active',
      },
      'surface-tooltip': {
        value: 'var(--w-color-grey-500)',
        bgUtility: 'w-bg-surface-tooltip',
        textUtility: 'w-text-surface-tooltip',
        cssVariable: '--w-color-surface-tooltip',
      },
      'surface-button-default': {
        value: 'var(--w-color-secondary)',
        bgUtility: 'w-bg-surface-button-default',
        textUtility: 'w-text-surface-button-default',
        cssVariable: '--w-color-surface-button-default',
      },
      'surface-button-hover': {
        value: 'var(--w-color-secondary-400)',
        bgUtility: 'w-bg-surface-button-hover',
        textUtility: 'w-text-surface-button-hover',
        cssVariable: '--w-color-surface-button-hover',
      },
      'surface-button-inactive': {
        value: 'var(--w-color-grey-400)',
        bgUtility: 'w-bg-surface-button-inactive',
        textUtility: 'w-text-surface-button-inactive',
        cssVariable: '--w-color-surface-button-inactive',
      },
      'surface-button-outline-hover': {
        value: 'var(--w-color-grey-500)',
        bgUtility: 'w-bg-surface-button-outline-hover',
        textUtility: 'w-text-surface-button-outline-hover',
        cssVariable: '--w-color-surface-button-outline-hover',
      },
    },
  },
  {
    label: 'Text',
    tokens: {
      'text-button': {
        value: 'var(--w-color-white)',
        bgUtility: 'w-bg-text-button',
        textUtility: 'w-text-text-button',
        cssVariable: '--w-color-text-button',
      },
      'text-label-menus-default': {
        value: 'var(--w-color-white-80)',
        bgUtility: 'w-bg-text-label-menus-default',
        textUtility: 'w-text-text-label-menus-default',
        cssVariable: '--w-color-text-label-menus-default',
      },
      'text-label-menus-active': {
        value: 'var(--w-color-white)',
        bgUtility: 'w-bg-text-label-menus-active',
        textUtility: 'w-text-text-label-menus-active',
        cssVariable: '--w-color-text-label-menus-active',
      },
      'text-label': {
        value: 'var(--w-color-grey-150)',
        bgUtility: 'w-bg-text-label',
        textUtility: 'w-text-text-label',
        cssVariable: '--w-color-text-label',
      },
      'text-context': {
        value: 'var(--w-color-grey-50)',
        bgUtility: 'w-bg-text-context',
        textUtility: 'w-text-text-context',
        cssVariable: '--w-color-text-context',
      },
      'text-meta': {
        value: 'var(--w-color-grey-150)',
        bgUtility: 'w-bg-text-meta',
        textUtility: 'w-text-text-meta',
        cssVariable: '--w-color-text-meta',
      },
      'text-placeholder': {
        value: 'var(--w-color-grey-200)',
        bgUtility: 'w-bg-text-placeholder',
        textUtility: 'w-text-text-placeholder',
        cssVariable: '--w-color-text-placeholder',
      },
      'text-link-default': {
        value: 'var(--w-color-secondary-100)',
        bgUtility: 'w-bg-text-link-default',
        textUtility: 'w-text-text-link-default',
        cssVariable: '--w-color-text-link-default',
      },
      'text-link-hover': {
        value: 'var(--w-color-secondary-75)',
        bgUtility: 'w-bg-text-link-hover',
        textUtility: 'w-text-text-link-hover',
        cssVariable: '--w-color-text-link-hover',
      },
      'text-button-outline-default': {
        value: 'var(--w-color-secondary-100)',
        bgUtility: 'w-bg-text-button-outline-default',
        textUtility: 'w-text-text-button-outline-default',
        cssVariable: '--w-color-text-button-outline-default',
      },
      'text-highlight': {
        value: 'var(--w-color-secondary-400)',
        bgUtility: 'w-bg-text-highlight',
        textUtility: 'w-text-text-highlight',
        cssVariable: '--w-color-text-highlight',
      },
      'text-error': {
        value: 'var(--w-color-critical-100)',
        bgUtility: 'w-bg-text-error',
        textUtility: 'w-text-text-error',
        cssVariable: '--w-color-text-error',
      },
    },
  },
  {
    label: 'Icons',
    tokens: {
      'icon-primary': {
        value: 'var(--w-color-grey-150)',
        bgUtility: 'w-bg-icon-primary',
        textUtility: 'w-text-icon-primary',
        cssVariable: '--w-color-icon-primary',
      },
      'icon-primary-hover': {
        value: 'var(--w-color-grey-50)',
        bgUtility: 'w-bg-icon-primary-hover',
        textUtility: 'w-text-icon-primary-hover',
        cssVariable: '--w-color-icon-primary-hover',
      },
      'icon-secondary': {
        value: 'var(--w-color-grey-150)',
        bgUtility: 'w-bg-icon-secondary',
        textUtility: 'w-text-icon-secondary',
        cssVariable: '--w-color-icon-secondary',
      },
      'icon-secondary-hover': {
        value: 'var(--w-color-grey-50)',
        bgUtility: 'w-bg-icon-secondary-hover',
        textUtility: 'w-text-icon-secondary-hover',
        cssVariable: '--w-color-icon-secondary-hover',
      },
    },
  },
  {
    label: 'Borders',
    tokens: {
      'border-furniture': {
        value: 'var(--w-color-grey-500)',
        bgUtility: 'w-bg-border-furniture',
        textUtility: 'w-text-border-furniture',
        cssVariable: '--w-color-border-furniture',
      },
      'border-button-small-outline-default': {
        value: 'var(--w-color-grey-400)',
        bgUtility: 'w-bg-border-button-small-outline-default',
        textUtility: 'w-text-border-button-small-outline-default',
        cssVariable: '--w-color-border-button-small-outline-default',
      },
      'border-field-default': {
        value: 'var(--w-color-grey-400)',
        bgUtility: 'w-bg-border-field-default',
        textUtility: 'w-text-border-field-default',
        cssVariable: '--w-color-border-field-default',
      },
      'border-field-inactive': {
        value: 'var(--w-color-grey-500)',
        bgUtility: 'w-bg-border-field-inactive',
        textUtility: 'w-text-border-field-inactive',
        cssVariable: '--w-color-border-field-inactive',
      },
      'border-field-hover': {
        value: 'var(--w-color-grey-200)',
        bgUtility: 'w-bg-border-field-hover',
        textUtility: 'w-text-border-field-hover',
        cssVariable: '--w-color-border-field-hover',
      },
      'border-button-outline-default': {
        value: 'var(--w-color-secondary-100)',
        bgUtility: 'w-bg-border-button-outline-default',
        textUtility: 'w-text-border-button-outline-default',
        cssVariable: '--w-color-border-button-outline-default',
      },
    },
  },
  {
    label: 'Misc',
    tokens: {
      focus: focusToken,
    },
  },
];

module.exports = {
  light,
  dark,
};
