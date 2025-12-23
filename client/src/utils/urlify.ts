import config from './urlify.config.json';

const cache = {};

/**
 * Create a transliterate function based on the locale.
 *
 * @see https://translit.cc/ (useful for testing)
 * @see https://czo.gov.ua/en/translit (Ukrainian)
 * @see https://en.wikipedia.org/wiki/List_of_ISO_639_language_codes
 */
const createTransliterateFn = (locale = '') => {
  if (cache[locale]) return cache[locale];

  // prepare the language part of the locale for comparison only
  const [langCode] = locale.toLowerCase().split('-');

  const downcodeMapping = Object.fromEntries(
    config
      .map((item) => Object.entries(item))
      .flat()
      // with the key being split by :, removing the first item.
      .map(([key, value]) => {
        const [, ...languageCodes] = key.toLowerCase().split(':');
        return [languageCodes, value];
      })
      // sort based on the comparison of matched language codes
      .sort(([langCodesA = []] = [], [langCodesB = []] = []) => {
        const valA = langCodesA.includes(langCode);
        const valB = langCodesB.includes(langCode);
        if (valA && !valB) return -1;
        if (!valA && valB) return 1;
        return 0;
      })
      .flatMap(([, values]) => values)
      // reverse to give priority to the matched language mappings
      .reverse(),
  );

  const regex = new RegExp(Object.keys(downcodeMapping).join('|'), 'g');

  const fn = (str) => str.replace(regex, (item) => downcodeMapping[item]);
  cache[langCode] = fn;

  return fn;
};

/**
 * This util and the mapping is refined port of Django's urlify.js util.
 * Without the Regex polyfill & without running trim (assuming the trim will be run before if needed).
 * In addition, it contains better handling different target languages via the `locale` option.
 *
 * @see https://github.com/django/django/blob/main/django/contrib/admin/static/admin/js/urlify.js
 */
export const urlify = (
  originalStr: string,
  {
    allowUnicode = false,
    locale = 'en',
    numChars = 255,
  }: {
    allowUnicode?: boolean;
    locale?: string;
    numChars?: number;
  } = {},
) => {
  let str = originalStr;
  // changes, e.g., "Petty theft" to "petty-theft"
  if (!allowUnicode) {
    str = createTransliterateFn(locale)(str);
  }
  str = str.toLowerCase(); // convert to lowercase
  // if downcode doesn't hit, the char will be stripped here
  if (allowUnicode) {
    // Keep Unicode letters including both lowercase and uppercase
    // characters, whitespace, and dash; remove other characters.
    str = str.replace(/[^-_\p{L}\p{N}\s]/gu, '');
  } else {
    str = str.replace(/[^-\w\s]/g, ''); // remove unneeded chars
  }
  str = str.replace(/[-\s]+/g, '-'); // convert spaces to hyphens
  str = str.substring(0, numChars); // trim to first num_chars chars
  str = str.replace(/-+$/g, ''); // trim any trailing hyphens
  return str;
};
