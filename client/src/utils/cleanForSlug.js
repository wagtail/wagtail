export function cleanForSlug(val, useURLify) {
  if (useURLify) {
    // URLify performs extra processing on the string (e.g. removing stopwords) and is more suitable
    // for creating a slug from the title, rather than sanitising a slug entered manually
    // eslint-disable-next-line no-undef, new-cap
    const cleaned = URLify(val, 255, window.unicodeSlugsEnabled);

    // if the result is blank (e.g. because the title consisted entirely of stopwords),
    // fall through to the non-URLify method
    if (cleaned) {
      return cleaned;
    }
  }

  // just do the "replace"
  if (window.unicodeSlugsEnabled) {
    return val.replace(/\s/g, '-').replace(/[&/\\#,+()$~%.'":`@^!*?<>{}]/g, '').toLowerCase();
  }
  return val.replace(/\s/g, '-').replace(/[^A-Za-z0-9\-_]/g, '').toLowerCase();
}
