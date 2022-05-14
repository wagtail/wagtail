// eslint-disable-next-line @typescript-eslint/no-var-requires, import/no-extraneous-dependencies
const plugin = require('tailwindcss/plugin');

module.exports = plugin(({ addComponents, theme }) => {
  addComponents({
    // Scrollbar styling for firefox
    // https://developer.mozilla.org/en-US/docs/Web/CSS/scrollbar-color
    '.scrollbar-thin': {
      'scrollbarColor': `${theme('colors.grey.100')} ${theme(
        'colors.white.DEFAULT',
      )}`,
      'scrollbarWidth': 'thin',

      // Custom scrollbar styling for Safari & Chrome Windows / Mac / Android.
      '&::-webkit-scrollbar': {
        width: '5px',
        height: '5px',
      },
      '&::-webkit-scrollbar-button': {
        // Hide the scrollbar arrows on windows
        display: 'none',
      },
      '&::-webkit-scrollbar-thumb': {
        // Hide the scrollbar arrows on windows
        backgroundColor: theme('colors.grey.200'),
        borderRadius: theme('borderRadius.sm'),
      },
      '&::-webkit-scrollbar-track': {
        background: theme('colors.transparent'),
      },
    },
  });
});
