function getWagtailConfig() {
  try {
    return JSON.parse(document.getElementById('wagtail-config')?.textContent);
  } catch (err) {
    /* eslint-disable no-console */
    console.error('Error loading Wagtail config');
    console.error(err);
    /* eslint-enable no-console */

    // This shouldn't happen as the config is generated with json_script tag
    // from the server, but if for some reason the element does not contain
    // valid JSON, ignore it and return an empty object.
    return {};
  }
}

export const WAGTAIL_CONFIG = getWagtailConfig();

global.wagtailConfig = WAGTAIL_CONFIG;

export const { ADMIN_API } = WAGTAIL_CONFIG;
export const { ADMIN_URLS } = WAGTAIL_CONFIG;

// Maximum number of pages to load inside the explorer menu.
export const MAX_EXPLORER_PAGES = 200;

export const LOCALE_NAMES = new Map();

/* eslint-disable-next-line camelcase */
WAGTAIL_CONFIG.LOCALES.forEach(({ code, display_name }) => {
  LOCALE_NAMES.set(code, display_name);
});
