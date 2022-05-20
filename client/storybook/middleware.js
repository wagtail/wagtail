/* eslint-disable @typescript-eslint/no-var-requires, import/no-extraneous-dependencies */
const middleware = require('storybook-django/src/middleware');

const origin = process.env.TEST_ORIGIN ?? 'http://localhost:8000';

module.exports = middleware.createDjangoAPIMiddleware({
  origin,
  // Must match the patterns in urls.py.
  apiPath: ['/pattern-library/', '/static/wagtailadmin/'],
});
