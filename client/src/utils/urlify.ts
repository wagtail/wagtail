import config from './urlify.config.json';

const downcodeMapping = config.reduce((acc, downcodeMap) => {
  Object.values(downcodeMap)
    .flat()
    .forEach(([char, replacedChar]) => {
      acc[char] = replacedChar;
    });
  return acc;
}, {});

const regex = new RegExp(Object.keys(downcodeMapping).join('|'), 'g');

/**
 * IMPORTANT This util and the mapping is a direct port of Django's urlify.js util,
 * without the need for a full Regex polyfill implementation.
 * @see https://github.com/django/django/blob/main/django/contrib/admin/static/admin/js/urlify.js
 */
export const urlify = (
  originalStr: string,
  {
    numChars = 255,
    allowUnicode = false,
  }: { numChars?: number; allowUnicode?: boolean } = {},
) => {
  let str = originalStr;
  // changes, e.g., "Petty theft" to "petty-theft"
  if (!allowUnicode) {
    str = str.replace(regex, (item) => downcodeMapping[item]);
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
  str = str.replace(/^\s+|\s+$/g, ''); // trim leading/trailing spaces
  str = str.replace(/[-\s]+/g, '-'); // convert spaces to hyphens
  str = str.substring(0, numChars); // trim to first num_chars chars
  str = str.replace(/-+$/g, ''); // trim any trailing hyphens
  return str;
};
