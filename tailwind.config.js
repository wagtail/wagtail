module.exports = {
  content: [
    './wagtail/**!(static)/*.{html,js,jsx,ts,tsx}', // Avoid purging compiled static assets
    './client/**/*.{html,js,jsx,ts,tsx}',
    './docs/**/*.{html,js,jsx,ts,tsx}',
  ],
  prefix: 'w-',
  theme: {
    extend: {},
  },
  plugins: [],
};
