// Language-sensitive string comparison.
// See https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/Collator/Collator.
const collator = new Intl.Collator(undefined, {
  usage: 'search',
  sensitivity: 'base',
  ignorePunctuation: true,
});

/**
 * Whether a string contains a subsring, with case-insensitive, locale-insensitive search.
 * See https://github.com/adobe/react-spectrum/blob/70e769acf639fc4ef3a704cb8fad81349cb4137a/packages/%40react-aria/i18n/src/useFilter.ts#L57.
 * See also https://github.com/arty-name/locale-index-of,
 * and https://github.com/tc39/ecma402/issues/506.
 */
export const contains = (string: string, substring: string) => {
  if (substring.length === 0) {
    return true;
  }

  const haystack = string.normalize('NFC');
  const needle = substring.normalize('NFC');

  for (let scan = 0; scan + needle.length <= haystack.length; scan += 1) {
    const slice = haystack.slice(scan, scan + needle.length);
    if (collator.compare(needle, slice) === 0) {
      return true;
    }
  }

  return false;
};

/**
 * Find all items where a search field matches the input.
 */
const findMatches = <T extends object>(
  items: T[],
  getSearchFields: (item: T) => (string | null | undefined)[],
  input: string,
) =>
  items.filter((item) => {
    const matches = getSearchFields(item);

    return matches.some((match) => match && contains(match, input));
  });

export default findMatches;
