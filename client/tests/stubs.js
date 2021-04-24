/**
 * Test stubs to mirror available global variables.
 * Those variables usually come from the back-end via templates.
 * See /wagtailadmin/templates/wagtailadmin/admin_base.html.
 */
import 'element-closest';

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
  STRINGS: {
    DELETE: 'Delete',
    EDIT: 'Edit',
    PAGE: 'Page',
    PAGES: 'Pages',
    LOADING: 'Loading…',
    NO_RESULTS: 'No results',
    SERVER_ERROR: 'Server Error',
    SEE_ALL: 'See all',
    CLOSE_EXPLORER: 'Close explorer',
    ALT_TEXT: 'Alt text',
    DECORATIVE_IMAGE: 'Decorative image',
    WRITE_HERE: 'Write here…',
    HORIZONTAL_LINE: 'Horizontal line',
    LINE_BREAK: 'Line break',
    UNDO: 'Undo',
    REDO: 'Redo',
    RELOAD_PAGE: 'Reload the page',
    RELOAD_EDITOR: 'Reload saved content',
    SHOW_LATEST_CONTENT: 'Show latest content',
    SHOW_ERROR: 'Show error',
    EDITOR_CRASH: 'The editor just crashed. Content has been reset to the last saved version.',
    BROKEN_LINK: 'Broken link',
    MISSING_DOCUMENT: 'Missing document',
    CLOSE: 'Close',
    EDIT_PAGE: 'Edit \'{title}\'',
    VIEW_CHILD_PAGES_OF_PAGE: 'View child pages of \'{title}\'',
    PAGE_EXPLORER: 'Page explorer',
    SAVE: 'Save',
    SAVING: 'Saving...',
    CANCEL: 'Cancel',
    DELETING: 'Deleting...',
    ADD_A_COMMENT: 'Add a comment',
    SHOW_COMMENTS: 'Show comments',
    REPLY: 'Reply',
    RESOLVE: 'Resolve',
    RETRY: 'Retry',
    DELETE_ERROR: 'Delete error',
    CONFIRM_DELETE_COMMENT: 'Are you sure?',
    SAVE_ERROR: 'Save error',
    SAVE_COMMENT_WARNING: 'This will be saved when the page is saved',
    FOCUS_COMMENT: 'Focus comment',
    UNFOCUS_COMMENT: 'Unfocus comment',
    SAVE_PAGE_TO_ADD_COMMENT: 'Save the page to add this comment',
    SAVE_PAGE_TO_SAVE_COMMENT_CHANGES: 'Save the page to save this comment',
    SAVE_PAGE_TO_SAVE_REPLY: 'Save the page to save this reply',
  },
  WAGTAIL_I18N_ENABLED: true,
  LOCALES: [
    {
      code: 'en',
      display_name: 'English'
    },
    {
      code: 'fr',
      display_nam: 'French'
    }
  ],
  ACTIVE_LOCALE: 'en'
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
