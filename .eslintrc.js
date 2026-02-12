/**
 * @see https://eslint.org/docs/user-guide/configuring
 * @type {import('eslint').Linter.Config}
 */
module.exports = {
  extends: [
    '@wagtail/eslint-config-wagtail',
    'plugin:@typescript-eslint/recommended',
    'plugin:storybook/recommended',
  ],
  parser: '@typescript-eslint/parser',
  plugins: ['@typescript-eslint', 'no-jquery'],
  env: {
    jest: true,
    browser: true,
  },
  rules: {
    '@typescript-eslint/explicit-function-return-type': 'off',
    '@typescript-eslint/explicit-member-accessibility': 'off',
    '@typescript-eslint/explicit-module-boundary-types': 'off',
    '@typescript-eslint/no-explicit-any': 'off',
    '@typescript-eslint/no-use-before-define': 'error',
    // it is often helpful to pull out logic to class methods that may not use `this`
    'class-methods-use-this': 'off',
    'import/extensions': [
      'error',
      'always',
      {
        ignorePackages: true,
        pattern: {
          js: 'never',
          jsx: 'never',
          ts: 'never',
          tsx: 'never',
        },
      },
    ],
    // does not align with the majority of legacy and newer code, some use named others use default exports
    'import/prefer-default-export': 'off',
    // allow no lines between single line members (e.g. static declarations)
    'lines-between-class-members': [
      'error',
      'always',
      { exceptAfterSingleLine: true },
    ],
    'max-classes-per-file': 'off',
    // Set warning for the top 5 jQuery rules to avoid new jQuery usage in code
    'no-jquery/no-ajax': 'warn',
    'no-jquery/no-global-selector': 'warn',
    'no-jquery/no-jquery-constructor': 'warn',
    'no-jquery/no-other-methods': 'warn',
    'no-jquery/no-other-utils': 'warn',
    // note you must disable the base rule as it can report incorrect errors
    'no-use-before-define': 'off',
    'no-underscore-dangle': [
      'error',
      { allow: ['__REDUX_DEVTOOLS_EXTENSION__', '_tippy'] },
    ],
    // this rule can be confusing as it forces some non-intuitive code for variable assignment
    'prefer-destructuring': 'off',
    'react/jsx-filename-extension': ['error', { extensions: ['.js', '.tsx'] }],
  },
  settings: {
    'import/core-modules': ['jquery'],
    'import/resolver': { node: { extensions: ['.js', '.ts', '.tsx'] } },
  },
  overrides: [
    // Rules that needs to be adjusted for TypeScript only files
    {
      files: ['*.ts'],
      rules: {
        '@typescript-eslint/no-shadow': 'error',
        'no-shadow': 'off',
      },
    },
    // Rules that we are ignoring currently due to legacy code in React components only
    {
      files: ['client/src/components/**'],
      rules: {
        'jsx-a11y/click-events-have-key-events': 'off',
        'jsx-a11y/interactive-supports-focus': 'off',
        'jsx-a11y/no-noninteractive-element-interactions': 'off',
        'react-hooks/exhaustive-deps': 'off',
        'react-hooks/rules-of-hooks': 'off',
        'react/button-has-type': 'off',
        'react/destructuring-assignment': 'off',
        'react/forbid-prop-types': 'off',
        'react/function-component-definition': 'off',
        'react/jsx-props-no-spreading': 'off',
        'react/no-danger': 'off',
        'react/no-deprecated': 'off',
        'react/require-default-props': 'off',
      },
    },
    // Rules we want to enforce or change for Stimulus Controllers
    {
      files: ['*Controller.ts'],
      rules: {
        '@typescript-eslint/member-ordering': [
          'error',
          {
            classes: {
              memberTypes: ['signature', 'field', 'method'],
            },
          },
        ],
        '@typescript-eslint/naming-convention': [
          'error',
          {
            selector: 'method',
            format: ['camelCase'],
            custom: {
              // Use connect or initialize instead of constructor, avoid generic 'render' or 'update' methods and instead be more specific.
              regex: '^(constructor|render|update)$',
              match: false,
            },
          },
          {
            selector: 'classProperty',
            format: ['camelCase'],
            custom: {
              // Use Stimulus values where possible for internal state, avoid a generic state object as these are not reactive.
              regex: '^(state)$',
              match: false,
            },
          },
        ],
        'no-restricted-properties': [
          'error',
          {
            object: 'window',
            property: 'Stimulus',
            message:
              "Please import the base Controller or only access the Stimulus instance via the controller's `this.application` attribute.",
          },
        ],
      },
    },
    // Rules we don’t want to enforce for test and tooling code.
    {
      files: [
        'client/extract-translatable-strings.js',
        'client/tests/**',
        'tailwind.config.js',
        'webpack.config.js',
        '*.stories.js',
        '*.stories.tsx',
        '*.test.js',
        '*.test.ts',
        '*.test.tsx',
        '**/storybook/**',
      ],
      rules: {
        '@typescript-eslint/no-empty-function': 'off',
        '@typescript-eslint/no-this-alias': 'off',
        '@typescript-eslint/no-unused-vars': 'off',
        '@typescript-eslint/no-var-requires': 'off',
        'global-require': 'off',
        'import/first': 'off',
        'import/no-extraneous-dependencies': 'off',
        'jsx-a11y/control-has-associated-label': 'off',
        'no-new': 'off',
        'no-unused-expressions': 'off',
        'react/function-component-definition': 'off',
        'react/jsx-props-no-spreading': 'off',
      },
    },
    // Files that use jquery via a global
    {
      files: [
        'wagtail/contrib/search_promotions/static_src/wagtailsearchpromotions/js/query-chooser-modal.js',
        'wagtail/contrib/search_promotions/templates/wagtailsearchpromotions/includes/searchpromotions_formset.js',
        'wagtail/contrib/search_promotions/templates/wagtailsearchpromotions/queries/chooser_field.js',
        'wagtail/documents/static_src/wagtaildocs/js/add-multiple.js',
        'wagtail/embeds/static_src/wagtailembeds/js/embed-chooser-modal.js',
        'wagtail/images/static_src/wagtailimages/js/add-multiple.js',
        'wagtail/images/static_src/wagtailimages/js/focal-point-chooser.js',
      ],
      globals: { $: 'readonly', jQuery: 'readonly' },
    },
    // Files that we will allow usage of jQuery (global or import) due to legacy code that will be refactored over time
    {
      files: [
        'client/src/components/Draftail/sources/ModalWorkflowSource.js',
        'client/src/components/ExpandingFormset/index.js',
        'client/src/components/InlinePanel/index.js',
        'client/src/components/StreamField/blocks/ActionButtons.ts',
        'client/src/components/StreamField/blocks/BaseSequenceBlock.js',
        'client/src/components/StreamField/blocks/FieldBlock.js',
        'client/src/components/StreamField/blocks/FieldBlock.test.js',
        'client/src/components/StreamField/blocks/ListBlock.js',
        'client/src/components/StreamField/blocks/ListBlock.test.js',
        'client/src/components/StreamField/blocks/StaticBlock.test.js',
        'client/src/components/StreamField/blocks/StreamBlock.js',
        'client/src/components/StreamField/blocks/StreamBlock.test.js',
        'client/src/components/StreamField/blocks/StructBlock.ts',
        'client/src/components/StreamField/blocks/StructBlock.test.js',
        'client/src/controllers/TagController.ts',
        'client/src/entrypoints/admin/filtered-select.js',
        'client/src/entrypoints/admin/modal-workflow.js',
        'client/src/entrypoints/admin/page-chooser-modal.js',
        'client/src/entrypoints/admin/privacy-switch.js',
        'client/src/entrypoints/admin/task-chooser-modal.js',
        'client/src/entrypoints/admin/task-chooser.js',
        'client/src/entrypoints/admin/workflow-action.js',
        'client/src/entrypoints/contrib/table_block/table.js',
        'client/src/entrypoints/contrib/table_block/table.test.js',
        'client/src/entrypoints/contrib/typed_table_block/typed_table_block.js',
        'client/src/entrypoints/contrib/typed_table_block/typed_table_block.test.js',
        'client/src/entrypoints/documents/document-chooser-modal.js',
        'client/src/entrypoints/images/image-chooser-modal.js',
        'client/src/includes/chooserModal.js',
        'client/src/includes/dateTimeChooser.js',
        'wagtail/contrib/search_promotions/static_src/wagtailsearchpromotions/js/query-chooser-modal.js',
        'wagtail/contrib/search_promotions/templates/wagtailsearchpromotions/includes/searchpromotions_formset.js',
        'wagtail/contrib/search_promotions/templates/wagtailsearchpromotions/queries/chooser_field.js',
        'wagtail/documents/static_src/wagtaildocs/js/add-multiple.js',
        'wagtail/embeds/static_src/wagtailembeds/js/embed-chooser-modal.js',
        'wagtail/images/static_src/wagtailimages/js/add-multiple.js',
        'wagtail/images/static_src/wagtailimages/js/focal-point-chooser.js',
      ],
      rules: {
        'no-jquery/no-ajax': 'off',
        'no-jquery/no-global-selector': 'off',
        'no-jquery/no-jquery-constructor': 'off',
        'no-jquery/no-other-methods': 'off',
        'no-jquery/no-other-utils': 'off',
      },
    },
    // Files that use other globals or legacy/vendor code that is unable to be easily linted
    {
      files: ['wagtail/**/**'],
      globals: {
        escapeHtml: 'readonly',
        ModalWorkflow: 'readonly',
        DOCUMENT_CHOOSER_MODAL_ONLOAD_HANDLERS: 'writable',
        EMBED_CHOOSER_MODAL_ONLOAD_HANDLERS: 'writable',
        IMAGE_CHOOSER_MODAL_ONLOAD_HANDLERS: 'writable',
        QUERY_CHOOSER_MODAL_ONLOAD_HANDLERS: 'writable',
        SNIPPET_CHOOSER_MODAL_ONLOAD_HANDLERS: 'writable',
      },
      rules: {
        '@typescript-eslint/no-unused-vars': 'off',
        '@typescript-eslint/no-use-before-define': 'off',
        'camelcase': [
          'error',
          {
            allow: [
              '__unused_webpack_module',
              '__webpack_modules__',
              '__webpack_require__',
            ],
            properties: 'never',
          },
        ],
        'consistent-return': 'off',
        'func-names': 'off',
        'id-length': 'off',
        'no-underscore-dangle': 'off',
        'object-shorthand': 'off',
        'prefer-arrow-callback': 'off',
        'vars-on-top': 'off',
      },
    },
  ],
};
