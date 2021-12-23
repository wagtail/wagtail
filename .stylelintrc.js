module.exports = {
  extends: '@wagtail/stylelint-config-wagtail',
  rules: {
    // Would be valuable for strict BEM components but is too hard to enforce with legacy code.
    'no-descending-specificity': null,
  },
};
