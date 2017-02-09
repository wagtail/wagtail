/**
 * Test stubs to mirror available global variables.
 * Those variables usually come from the back-end via templates.
 * See /wagtailadmin/templates/wagtailadmin/admin_base.html.
 */

global.wagtailConfig = {
  ADMIN_API: {
    DOCUMENTS: '/admin/api/v2beta/documents/',
    IMAGES: '/admin/api/v2beta/images/',
    PAGES: '/admin/api/v2beta/pages/',
  },
  ADMIN_URLS: {
    PAGES: '/admin/pages/',
  },
  DATE_FORMATTING: {
    DATE_FORMAT: 'MMM. D, YYYY',
    SHORT_DATE_FORMAT: 'DD/MM/YYYY',
  },
  STRINGS: {
    EXPLORER: 'Explorer',
    LOADING: 'Loading...',
    NO_RESULTS: 'No results',
    SEE_CHILDREN: 'See Children',
    NO_DATE: 'No date',
  },
};

global.wagtailVersion = '1.6a1';
