// https://docs.djangoproject.com/en/3.1/topics/i18n/translation/#gettext
export function gettext(text: string): string {
  const djangoGettext = (window as any).django?.gettext;

  if (djangoGettext) {
    return djangoGettext(text);
  }

  return text;
}

// https://docs.djangoproject.com/en/3.1/topics/i18n/translation/#ngettext
export function ngettext(text: string): string {
  const djangoNgettext = (window as any).django?.ngettext;

  if (djangoNgettext) {
    return djangoNgettext(text);
  }

  return text;
}

// https://docs.djangoproject.com/en/3.1/topics/i18n/translation/#get-format
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

export function getFormat(formatType: FormatType): string {
  const djangoGetFormat = (window as any).django?.get_format;

  if (djangoGetFormat) {
    return djangoGetFormat(formatType);
  }

  return '';
}

// https://docs.djangoproject.com/en/3.1/topics/i18n/translation/#gettext_noop
export function gettextNoop(text: string): string {
  const djangoGettextNoop = (window as any).django?.gettext_noop;

  if (djangoGettextNoop) {
    return djangoGettextNoop(text);
  }

  return text;
}

// https://docs.djangoproject.com/en/3.1/topics/i18n/translation/#pluralidx
export function pluralIdx(count: number): boolean {
  const djangoPluralIdx = (window as any).django?.pluralidx;

  if (djangoPluralIdx) {
    return djangoPluralIdx(count);
  }

  return false;
}
