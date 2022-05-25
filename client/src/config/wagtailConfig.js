export const { ADMIN_API } = global.wagtailConfig;
export const { ADMIN_URLS } = global.wagtailConfig;

// Maximum number of pages to load inside the explorer menu.
export const MAX_EXPLORER_PAGES = 200;

export const LOCALE_NAMES = new Map();

/* eslint-disable-next-line camelcase */
global.wagtailConfig.LOCALES.forEach(({ code, display_name }) => {
  LOCALE_NAMES.set(code, display_name);
});
