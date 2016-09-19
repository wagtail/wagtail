/**
 * Test stubs to mirror available global variables.
 * Those variables usually come from the back-end via templates.
 * See /wagtailadmin/templates/wagtailadmin/admin_base.html.
 */

global.wagtailConfig = {
  api: {
    documents: '/admin/api/v1beta/documents/',
    images: '/admin/api/v1beta/images/',
    pages: '/admin/api/v1beta/pages/',
  },
  urls: {
    pages: '/admin/pages/',
  },
  strings: {
    EXPLORER: 'Explorer',
    LOADING: 'Loading...',
    NO_RESULTS: 'No results',
    SEE_CHILDREN: 'See Children',
  },
};

global.wagtailVersion = '1.6a1';
