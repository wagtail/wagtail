/**
 * Returns the supplied string as a slug, accepts options.unicodeSlugsEnabled to support
 * additional characters being allowed.
 */

/** The Function sanitizeSlug is to remove the unwanted characters of other languages which are not
 * validated by django's validator
 */

function sanitizeSlug(input: string): string {
  // Define a regular expression to match allowed characters including Unicode letters and numbers
  const allowedCharacters = /^[\p{L}\p{N}_-]+$/u;

  // Replace disallowed characters with an empty string
  const sanitized = input
      .split('') // Split into individual characters
      .filter(char => allowedCharacters.test(char)) // Keep only allowed characters
      .join(''); // Join back into a string

  return sanitized;
}

export const slugify = (
  value: string,
  { allowUnicode = false }: { allowUnicode?: boolean } = {},
) =>
  {
  const slug = allowUnicode
    ? 
    value
        .replace(/\s+/g, '-')
        .replace(/[&/\\#,+()$~%.'":`@^!*?<>{}]/g, '')
        .toLowerCase()
    : value
        .replace(/\s+/g, '-')
        .replace(/[^A-Za-z0-9\-_]/g, '')
        .toLowerCase();
      return allowUnicode ? sanitizeSlug(slug) : slug;
  };