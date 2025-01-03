import { Controller } from '@hotwired/stimulus';

export class LocaleController extends Controller<HTMLSelectElement> {
  localizeTimeZoneOptions(
    event?: Event & { params?: { serverTimeZone?: string } },
  ) {
    const serverTimeZone = event?.params?.serverTimeZone;
    Array.from(this.element.options).forEach((option) => {
      const localized = option.value
        ? LocaleController.getTZLabel(option.value)
        : LocaleController.getTZLabel(serverTimeZone || '');
      // eslint-disable-next-line no-param-reassign
      option.innerText = `${option.innerText}: ${localized}`;
    });
  }

  static getTZLabel(timeZone: string) {
    const shortLabel = this.localizeTimeZone(timeZone, 'short');
    const longLabel = this.localizeTimeZone(timeZone, 'long');
    return `${shortLabel} (${longLabel})`;
  }

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
}
