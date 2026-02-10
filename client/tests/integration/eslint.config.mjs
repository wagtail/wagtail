/**
 * ESLint configuration for integration tests
 * This extends the base flat config with test-specific overrides
 */

import globals from 'globals';
import baseConfig from '../../../eslint.config.mjs';

export default [
  ...baseConfig,
  {
    languageOptions: {
      globals: {
        ...globals.node,
        page: 'readonly',
        TEST_ORIGIN: 'readonly',
        __BROWSER_GLOBAL__: 'readonly',
      },
    },
    rules: {
      // To support code running in Node without transpiling
      '@typescript-eslint/no-require-imports': 'off',
      'no-underscore-dangle': ['error', { allow: ['__BROWSER_GLOBAL__'] }],
      // So we can lint the code without resolving imports, in case the sub-package isn't installed
      'import-x/no-extraneous-dependencies': 'off',
      'import-x/no-relative-packages': 'off',
      'import-x/no-unresolved': 'off',
    },
  },
];
