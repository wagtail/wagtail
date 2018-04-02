/**
 * Test stubs to mirror available global variables.
 * Those variables usually come from the back-end via templates.
 * See /wagtailadmin/templates/wagtailadmin/admin_base.html.
 */
import 'element-closest';

global.wagtailConfig = {
  ADMIN_API: {
    DOCUMENTS: '/admin/api/v2beta/documents/',
    IMAGES: '/admin/api/v2beta/images/',
    PAGES: '/admin/api/v2beta/pages/',
    EXTRA_CHILDREN_PARAMETERS: '',
  },
  ADMIN_URLS: {
    PAGES: '/admin/pages/',
  },
  DATE_FORMATTING: {
    DATE_FORMAT: 'MMM. D, YYYY',
    SHORT_DATE_FORMAT: 'DD/MM/YYYY',
  },
  STRINGS: {
    EDIT: 'Edit',
    DELETE: 'Delete',
    PAGE: 'Page',
    PAGES: 'Pages',
    LOADING: 'Loading…',
    NO_RESULTS: 'No results',
    SERVER_ERROR: 'Server Error',
    SEE_CHILDREN: 'See children',
    SEE_ALL: 'See all',
    CLOSE_EXPLORER: 'Close explorer',
    ALT_TEXT: 'Alt text',
    WRITE_HERE: 'Write here…',
    HORIZONTAL_LINE: 'Horizontal line',
    LINE_BREAK: 'Line break',
    UNDO: 'Undo',
    REDO: 'Redo',
    RELOAD_PAGE: 'Reload the page',
    RELOAD_EDITOR: 'Reload saved content',
    SHOW_LATEST_CONTENT: 'Show latest content',
    EDITOR_CRASH: 'The editor just crashed. Content has been reset to the last saved version.',
  },
};

global.wagtailVersion = '1.6a1';

global.chooserUrls = {
  documentChooser: '/admin/documents/chooser/',
  emailLinkChooser: '/admin/choose-email-link/',
  embedsChooser: '/admin/embeds/chooser/',
  externalLinkChooser: '/admin/choose-external-link/',
  imageChooser: '/admin/images/chooser/',
  pageChooser: '/admin/choose-page/',
  snippetChooser: '/admin/snippets/choose/',
};

const jQueryObj = {
  on: jest.fn(),
  off: jest.fn(),
};

global.jQuery = () => jQueryObj;
