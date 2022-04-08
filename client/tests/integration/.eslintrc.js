/**
 * Overrides to our base ESLint configuration specifically for our integration tests.
 */
module.exports = {
  rules: {
    // To support code running in Node without transpiling.
    '@typescript-eslint/no-var-requires': 'off',
    'no-underscore-dangle': ['error', { allow: ['__BROWSER_GLOBAL__'] }],
    // So we can lint the code without resolving imports, in case the sub-package isn’t installed.
    'import/no-unresolved': 'off',
  },
  env: {
    jest: true,
    browser: true,
    node: true,
  },
  globals: {
    page: 'readonly',
    TEST_ORIGIN: 'readonly',
  },
};
