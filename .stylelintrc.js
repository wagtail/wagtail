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
  },
};
