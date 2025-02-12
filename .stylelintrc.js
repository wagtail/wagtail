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
    // Refined ordering to align with media mixin usage - see https://github.com/wagtail/stylelint-config-wagtail/issues/37
    'order/order': ['dollar-variables', 'custom-properties', 'declarations'],
    // Some parts of declaration-strict-value commented out until we are in a position to enforce them.
    'scale-unlimited/declaration-strict-value': [
      [
        // Colors should always be defined from variables or functions.
        '/color/',
        'fill',
        'stroke',
        // Font tokens should come from our design tokens.
        'font-family',
        // 'font-size',
        // 'font-weight',
        // Spacing should use a consistent scale rather than hard-coded values.
        // '/margin/',
        // '/padding/',
        // 'gap',
        // Consistently using variables for z-index allows us to define the order of the values globally.
        // 'z-index',
      ],
      {
        disableFix: true,
        ignoreValues: [
          'currentColor',
          'inherit',
          'initial',
          'none',
          'unset',
          'transparent',
          'normal',
          // System colors for forced-colors styling.
          // See https://drafts.csswg.org/css-color-4/#css-system-colors.
          'Canvas',
          'CanvasText',
          'LinkText',
          'VisitedText',
          'ActiveText',
          'ButtonFace',
          'ButtonText',
          'ButtonBorder',
          'Field',
          'FieldText',
          'Highlight',
          'HighlightText',
          'SelectedItem',
          'SelectedItemText',
          'Mark',
          'MarkText',
          'GrayText',
          'AccentColor',
          'AccentColorText',
        ],
      },
    ],
    // Ignore rule until all existing selectors can be updated.
    'scss/selector-no-union-class-name': null,
    // Ignore rule until all existing classes can be updated to use BEM.
    'selector-class-pattern': null,
    // Allow more specificity until styles can be updated to match the more strict rules.
    'selector-max-specificity': '0,6,3',
    // Ignore rule until we confirmed we prefer shorthand properties for positioning.
    'declaration-block-no-redundant-longhand-properties': null,
  },
};
