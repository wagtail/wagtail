module.exports = {
  content: [
    './wagtail/**!(static)/*.{html,js,jsx,ts,tsx}', // Avoid purging compiled static assets
    './client/**/*.{html,js,ts,tsx}',
    './docs/**/*.{html,js,ts,tsx}',
  ],
  prefix: 'w-',
  theme: {
    extend: {},
  },
  plugins: [],
};
