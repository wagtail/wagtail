/**
 * Returns the supplied string as a slug, accepts options.unicodeSlugsEnabled to support
 * additional characters being allowed.
 */
export const slugify = (
  value: string,
  { allowUnicode = false }: { allowUnicode?: boolean } = {},
) =>
  allowUnicode
    ? value
        .replace(/\s+/g, '-')
        .replace(/[&/\\#,+()$~%.'":`@^!*?<>{}]/g, '')
        .toLowerCase()
    : value
        .replace(/\s+/g, '-')
        .replace(/[^A-Za-z0-9\-_]/g, '')
        .toLowerCase();
