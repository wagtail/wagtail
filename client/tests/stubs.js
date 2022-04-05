/**
 * Test stubs to mirror available global variables.
 * Those variables usually come from the back-end via templates.
 * See /wagtailadmin/templates/wagtailadmin/admin_base.html.
 */

global.wagtailConfig = {
  ADMIN_API: {
    DOCUMENTS: '/admin/api/main/documents/',
    IMAGES: '/admin/api/main/images/',
    PAGES: '/admin/api/main/pages/',
    EXTRA_CHILDREN_PARAMETERS: '',
  },
  ADMIN_URLS: {
    PAGES: '/admin/pages/',
  },
  DATE_FORMATTING: {
    DATE_FORMAT: 'MMM. D, YYYY',
    SHORT_DATE_FORMAT: 'DD/MM/YYYY',
  },
  WAGTAIL_I18N_ENABLED: true,
  LOCALES: [
    {
      code: 'en',
      display_name: 'English',
    },
    {
      code: 'fr',
      display_nam: 'French',
    },
  ],
  ACTIVE_LOCALE: 'en',
};

global.wagtailVersion = '1.6a1';

global.wagtail = {};

global.chooserUrls = {
  documentChooser: '/admin/documents/chooser/',
  emailLinkChooser: '/admin/choose-email-link/',
  anchorLinkChooser: '/admin/choose-anchor-link',
  embedsChooser: '/admin/embeds/chooser/',
  externalLinkChooser: '/admin/choose-external-link/',
  imageChooser: '/admin/images/chooser/',
  pageChooser: '/admin/choose-page/',
};

/* use dummy content for onload handlers just so that we can verify that we've chosen the right one */
global.IMAGE_CHOOSER_MODAL_ONLOAD_HANDLERS = { type: 'image' };
global.PAGE_CHOOSER_MODAL_ONLOAD_HANDLERS = { type: 'page' };
global.EMBED_CHOOSER_MODAL_ONLOAD_HANDLERS = { type: 'embed' };
global.DOCUMENT_CHOOSER_MODAL_ONLOAD_HANDLERS = { type: 'document' };
