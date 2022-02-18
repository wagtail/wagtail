/* eslint-disable @typescript-eslint/no-var-requires */
const middleware = require('storybook-django/src/middleware');

const origin = process.env.TEST_ORIGIN ?? 'http://localhost:8000';

module.exports = middleware.createDjangoAPIMiddleware({
  origin,
  // Must match the urls.py pattern for the pattern library.
  apiPath: '/pattern-library/',
});
