import { Controller } from '@hotwired/stimulus';

/**
 * Localizes elements in the current locale.
 *
 * @example
 * ```html
 * <select data-controller="w-locale" data-action="w-locale#localizeTimeZoneOptions">
 *   <option value="" selected>Use server time zone</option>
 *   <option value="Asia/Jakarta">Asia/Jakarta</option>
 *   <option value="Asia/Tokyo">Asia/Tokyo</option>
 * </select>
 * ```
 */
export class LocaleController extends Controller<HTMLSelectElement> {
  /**
   * Localize an IANA time zone in the current locale.
   *
   * @param timeZone An IANA time zone string
   * @param format Time zone name formatting option
   * @returns formatted time zone name in the current locale
   */
  static localizeTimeZone(
    timeZone: string,
    format: Intl.DateTimeFormatOptions['timeZoneName'],
  ) {
    const df = new Intl.DateTimeFormat(document.documentElement.lang, {
      timeZone,
      timeZoneName: format,
    });
    const parts = df.formatToParts(new Date());
    return parts.find((part) => part.type === 'timeZoneName')!.value;
  }

  /**
   *
   * @param timeZone An IANA time zone string
   * @returns formatted time zone name in the current locale with short and long
   * labels, e.g. `"GMT+7 (Western Indonesia Time)"`
   */
  static getTZLabel(timeZone: string) {
    const shortLabel = LocaleController.localizeTimeZone(timeZone, 'short');
    const longLabel = LocaleController.localizeTimeZone(timeZone, 'long');
    return `${shortLabel} (${longLabel})`;
  }

  /**
   * Localize the time zone `<options>` of a `<select>` element in the current
   * locale.
   */
  localizeTimeZoneOptions(
    event?: Event & { params?: { serverTimeZone?: string } },
  ) {
    const element = (event?.target as HTMLSelectElement) || this.element;
    const serverTimeZone = event?.params?.serverTimeZone;
    Array.from(element.options).forEach((opt) => {
      const timeZone = opt.value || serverTimeZone;
      if (!timeZone) return;
      const localized = LocaleController.getTZLabel(timeZone);
      const option = opt;
      option.textContent = `${option.textContent}: ${localized}`;
    });
  }
}
