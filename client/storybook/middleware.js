const middleware = require('storybook-django/src/middleware');

// Target the Django server with IPV4 address explicitly to avoid DNS resolution of localhost to IPV6.
const origin = process.env.TEST_ORIGIN ?? 'http://127.0.0.1:8000';

module.exports = middleware.createDjangoAPIMiddleware({
  origin,
  // Must match the patterns in urls.py.
  apiPath: ['/pattern-library/', '/static/wagtailadmin/'],
});
