import { slugify } from './slugify';

declare global {
  interface Window {
    URLify: any;
  }
}

/**
 * Returns the supplied string as a slug suitable for a URL using the vendor URLify util.
 * If the vendor util returns an empty string it will fall back to the slugify method.
 */
export const urlify = (value: string, options = {}) => {
  // URLify performs extra processing on the string (e.g. removing stopwords) and is more suitable
  // for creating a slug from the title, rather than sanitising a slug entered manually
  const cleaned = window.URLify(value, 255);

  // if the result is blank (e.g. because the title consisted entirely of stopwords),
  // fall through to the non-URLify method
  return cleaned || slugify(value, options);
};
