/**
 * Translation / Internationalisation utilities based on Django's `JavaScriptCatalogView`
 *
 * https://docs.djangoproject.com/en/stable/topics/i18n/translation/#module-django.views.i18n
 */

/**
 * The gettext function behaves similarly to the standard gettext interface within Django.
 *
 * https://docs.djangoproject.com/en/stable/topics/i18n/translation/#gettext
 *
 * @param {string} text
 * @returns {string}
 */
export function gettext(text: string): string {
  const djangoGettext = (window as any).django?.gettext;

  if (djangoGettext) {
    return djangoGettext(text);
  }

  return text;
}

/**
 * The ngettext function provides an interface to pluralize words and phrases.
 *
 * https://docs.djangoproject.com/en/stable/topics/i18n/translation/#ngettext
 *
 * @param {string} singular
 * @param {string} plural
 * @param {number} count
 * @returns {string}
 *
 * @example
 * const ngettext('one bird', 'two or more in the hand', 2);
 * // 'two or more in the hand'
 *
 */
export function ngettext(
  singular: string,
  plural: string,
  count: number,
): string {
  const djangoNgettext = (window as any).django?.ngettext;

  if (djangoNgettext) {
    return djangoNgettext(singular, plural, count);
  }

  return singular;
}

/**
 * https://docs.djangoproject.com/en/stable/topics/i18n/translation/#get-format
 */
export type FormatType =
  | 'DATE_FORMAT'
  | 'DATE_INPUT_FORMATS'
  | 'DATETIME_FORMAT'
  | 'DATETIME_INPUT_FORMATS'
  | 'DECIMAL_SEPARATOR'
  | 'FIRST_DAY_OF_WEEK'
  | 'MONTH_DAY_FORMAT'
  | 'NUMBER_GROUPING'
  | 'SHORT_DATE_FORMAT'
  | 'SHORT_DATETIME_FORMAT'
  | 'THOUSAND_SEPARATOR'
  | 'TIME_FORMAT'
  | 'TIME_INPUT_FORMATS'
  | 'YEAR_MONTH_FORMAT';

/**
 * The getFormat function has access to the configured i18n formatting settings and
 * can retrieve the format string for a given setting name.
 *
 * https://docs.djangoproject.com/en/stable/topics/i18n/translation/#get-format
 *
 * @param {FormatType} formatType
 * @returns {str}
 *
 * @example
 * get_format('DATE_FORMAT');
 * // 'N j, Y'
 *
 */
export function getFormat(formatType: FormatType): string {
  const djangoGetFormat = (window as any).django?.get_format;

  if (djangoGetFormat) {
    return djangoGetFormat(formatType);
  }

  return '';
}

/**
 * Marks strings for translation but doesn’t translate them now.
 * This can be used to store strings in global variables that should stay in the base
 * language (because they might be used externally) and will be translated later.
 *
 * https://docs.djangoproject.com/en/stable/topics/i18n/translation/#gettext_noop
 *
 * @param {string} text
 * @returns {string}
 */
export function gettextNoop(text: string): string {
  const djangoGettextNoop = (window as any).django?.gettext_noop;

  if (djangoGettextNoop) {
    return djangoGettextNoop(text);
  }

  return text;
}

/**
 * The pluralidx function works in a similar way to the pluralize template filter,
 * determining if a given count should use a plural form of a word or not.
 *
 * https://docs.djangoproject.com/en/stable/topics/i18n/translation/#pluralidx
 *
 * @param {number} count
 * @returns {boolean}
 *
 * @example
 * pluralidx(0);
 * // true
 * pluralidx(1);
 * // false
 * pluralidx(2);
 * // true
 *
 */
export function pluralIdx(count: number): boolean {
  const djangoPluralIdx = (window as any).django?.pluralidx;

  if (djangoPluralIdx) {
    return djangoPluralIdx(count);
  }

  return false;
}
