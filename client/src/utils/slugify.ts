/**
 * Returns the supplied string as a slug, accepts options.allowUnicode to support
 * additional characters being allowed.
 * Special characters of other languages which are not validated by django's slug validator are discarded.
 */
export const slugify = (
  value: string,
  { allowUnicode = false }: { allowUnicode?: boolean } = {},
) => {
  let slug: string;
  const allowedCharacters = /^[\p{L}\p{N}_-]+$/u;

  if (allowUnicode) {
    slug = value
      .replace(/\s+/g, '-')
      .toLowerCase()
      .split('')
      .filter((char) => allowedCharacters.test(char))
      .join('');
  } else {
    slug = value
      .replace(/\s+/g, '-')
      .replace(/[^A-Za-z0-9\-_]/g, '')
      .toLowerCase();
  }

  return slug;
};
