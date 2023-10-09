/* eslint no-restricted-globals: ["error", { "name": "jest", "message": "jest is not available in Storybook." }] */

/**
 * Test stubs to mirror available global variables in Jest tests
 * and Storybook, avoid using the jest global as this is not
 * available in Storybook.
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

const script = document.createElement('script');
script.type = 'application/json';
script.id = 'wagtail-config';
script.textContent = JSON.stringify({ CSRF_TOKEN: 'potato' });
document.body.appendChild(script);

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

class PageChooserModal {}
global.PageChooserModal = PageChooserModal;

/** Mock window.scrollTo as not provided via JSDom */
window.scrollTo = () => {};

/** Mock console.warn to filter out warnings from React due to Draftail legacy Component API usage.
 * Draftail/Draft-js is unlikely to support these and the warnings are not useful for unit test output.
 */
/* eslint-disable no-console */
const consoleWarnOriginal = console.warn;
console.warn = function filterWarnings(...args) {
  /* eslint-enable no-console */

  const [warning, component] = args;

  const legacyReactWarnings = [
    'Warning: componentWillMount has been renamed, and is not recommended for use.',
    'Warning: componentWillReceiveProps has been renamed, and is not recommended for use.',
    'Warning: componentWillUpdate has been renamed, and is not recommended for use.',
  ];

  const ignoredComponents = ['DraftEditor', 'PluginEditor'];

  if (
    legacyReactWarnings.some((_) => warning.includes(_)) &&
    ignoredComponents.includes(component)
  ) {
    return;
  }

  consoleWarnOriginal.apply(console, args);
};
