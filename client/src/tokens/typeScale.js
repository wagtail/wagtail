// eslint-disable-next-line @typescript-eslint/no-var-requires
const plugin = require('tailwindcss/plugin');

// TypeScale plugin:
// This plugin generates component classes using tailwind's configuration for each object inside of the typeScale const.
// If the tailwind config is using a prefix such as 'w-' this will be included in the compiled css class eg. .w-h1
module.exports = plugin(({ addComponents, theme }) => {
  const headingBaseStyles = {
    fontWeight: theme('fontWeight.bold'),
    color: theme('colors.primary.DEFAULT'),
    lineHeight: theme('lineHeight.tight'),
  };

  const typeScale = {
    '.h1': {
      fontSize: theme('fontSize.30'),
      fontWeight: theme('fontWeight.extrabold'),
      color: theme('colors.primary.DEFAULT'),
      lineHeight: theme('lineHeight.tight'),
    },
    '.h2': {
      fontSize: theme('fontSize.24'),
      ...headingBaseStyles,
    },
    '.h3': {
      fontSize: theme('fontSize.22'),
      ...headingBaseStyles,
    },
    '.h4': {
      fontSize: theme('fontSize.18'),
      ...headingBaseStyles,
    },
    '.label-1': {
      fontSize: theme('fontSize.16'),
      fontWeight: theme('fontWeight.bold'),
      color: theme('colors.primary.DEFAULT'),
      lineHeight: theme('lineHeight.tight'),
    },
    '.label-2': {
      fontSize: theme('fontSize.15'),
      fontWeight: theme('fontWeight.semibold'),
      color: theme('colors.primary.DEFAULT'),
      lineHeight: theme('lineHeight.tight'),
    },
    '.label-3': {
      fontSize: theme('fontSize.14'),
      fontWeight: theme('fontWeight.medium'),
      color: theme('colors.primary.DEFAULT'),
      lineHeight: theme('lineHeight.tight'),
    },
    '.body-text': {
      fontSize: theme('fontSize.16'),
      fontWeight: theme('fontWeight.normal'),
      lineHeight: theme('lineHeight.normal'),
    },
    '.body-text-large': {
      fontSize: theme('fontSize.18'),
      fontWeight: theme('fontWeight.normal'),
      lineHeight: theme('lineHeight.normal'),
    },
    '.help-text': {
      fontSize: theme('fontSize.14'),
      fontWeight: theme('fontWeight.normal'),
      color: theme('colors.grey.400'),
      lineHeight: theme('lineHeight.tight'),
    },
  };

  addComponents(typeScale);
});
