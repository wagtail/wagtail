module.exports = {
  extends: '@wagtail/stylelint-config-wagtail',
  rules: {
    'scss/at-rule-no-unknown': [
      true,
      {
        ignoreAtRules: [
          'tailwind',
          'apply',
          'variants',
          'responsive',
          'screen',
          'layer',
        ],
      },
    ],
    'no-invalid-position-at-import-rule': [
      true,
      {
        ignoreAtRules: ['tailwind', 'use'],
      },
    ],
    // Would be valuable for strict BEM components but is too hard to enforce with legacy code.
    'no-descending-specificity': null,
    // Override stylelint-config-wagtail’s options to allow all float and clear values for now.
    'declaration-property-value-allowed-list': {
      // 'clear': ['both', 'none'],
      // 'float': ['inline-start', 'inline-end', 'none', 'unset'],
      'text-align': ['start', 'end', 'center'],
    },
    // Disable declaration-strict-value until we are in a position to enforce it.
    'scale-unlimited/declaration-strict-value': null,
  },
};
