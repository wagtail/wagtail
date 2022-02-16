module.exports = {
  content: [
    './{wagtail/templates/**/*.html',
    './{wagtail/static_src/**/*.{js,jsx,ts,tsx}',
    './{client/**/*.{html,js,jsx,ts,tsx}',
    './{docs/**/*.{html,js,jsx,ts,tsx}',
  ],
  prefix: 'w-',
  theme: {
    extend: {},
  },
  plugins: [],
};
