import { Application } from '@hotwired/stimulus';
import { InitController } from './InitController';
import { LocaleController } from './LocaleController';

// Ensure the labels are consistent with the snapshot regardless of DST.
jest.useFakeTimers();
jest.setSystemTime(new Date('2025-01-11'));

afterEach(() => {
  // clear any mocked globals after each test
  if (window.django) {
    delete window.django;
  }
});

beforeAll(() => {
  jest
    .spyOn(Intl, 'DateTimeFormat')
    .mockImplementation((locale, { timeZone, timeZoneName }) => ({
      formatToParts: jest.fn(() => [
        {
          type: 'timeZoneName',
          value: `${timeZone} in ${locale} with ${timeZoneName} format`,
        },
      ]),
    }));
});

afterAll(() => {
  Intl.DateTimeFormat.mockRestore();
});

describe('LocaleController', () => {
  let app;
  let select;

  const setup = async (html) => {
    document.body.innerHTML = `<main>${html}</main>`;
    select = document.querySelector('select');
    select.innerHTML = /* html */ `
      <option value="" selected>Use server time zone</option>
      <option value="Africa/Abidjan">Africa/Abidjan</option>
      <option value="America/Argentina/Jujuy">America/Argentina/Jujuy</option>
      <option value="America/Indiana/Knox">America/Indiana/Knox</option>
      <option value="Antarctica/Rothera">Antarctica/Rothera</option>
      <option value="Arctic/Longyearbyen">Arctic/Longyearbyen</option>
      <option value="Asia/Katmandu">Asia/Katmandu</option>
      <option value="Atlantic/Canary">Atlantic/Canary</option>
      <option value="Australia/South">Australia/South</option>
      <option value="Brazil/East">Brazil/East</option>
      <option value="Canada/Atlantic">Canada/Atlantic</option>
      <option value="Chile/Continental">Chile/Continental</option>
      <option value="EST">EST</option>
      <option value="Etc/GMT-7">Etc/GMT-7</option>
      <option value="Europe/Brussels">Europe/Brussels</option>
      <option value="GMT">GMT</option>
      <option value="Indian/Maldives">Indian/Maldives</option>
      <option value="Pacific/Tarawa">Pacific/Tarawa</option>
      <option value="UTC">UTC</option>
      <option value="Universal">Universal</option>
      <option value="Zulu">Zulu</option>
    `;

    app = Application.start();
    app.register('w-locale', LocaleController);
    app.register('w-init', InitController);

    await Promise.resolve();
  };

  afterEach(() => {
    app?.stop();
    jest.clearAllMocks();
  });

  describe('localizing time zone options', () => {
    it('should append localized time zone labels to the options', async () => {
      document.documentElement.lang = 'en-US';
      await setup(/* html */ `
        <select
          name="locale-current_time_zone"
          data-controller="w-init w-locale"
          data-action="w-init:ready->w-locale#localizeTimeZoneOptions"
          data-w-locale-server-time-zone-param="Europe/London"
        >
        </select>
      `);

      expect(select.getAttribute('data-controller')).toEqual('w-locale');
      const selected = select.selectedOptions[0];
      expect(selected).toBeTruthy();
      expect(selected.value).toEqual('');
      expect(selected.textContent).toEqual(
        'Use server time zone: Europe/London in en-US with short format (Europe/London in en-US with long format)',
      );

      expect(select).toMatchSnapshot();
    });
  });

  it('should localize to the current HTML locale and use the server time zone param for the default', async () => {
    document.documentElement.lang = 'id-ID';
    await setup(/* html */ `
      <select
        name="locale-current_time_zone"
        data-controller="w-init w-locale"
        data-action="w-init:ready->w-locale#localizeTimeZoneOptions"
        data-w-locale-server-time-zone-param="Asia/Jakarta"
      >
      </select>
    `);

    expect(select.getAttribute('data-controller')).toEqual('w-locale');
    const selected = select.selectedOptions[0];
    expect(selected).toBeTruthy();
    expect(selected.value).toEqual('');
    expect(selected.textContent).toEqual(
      'Use server time zone: Asia/Jakarta in id-ID with short format (Asia/Jakarta in id-ID with long format)',
    );
    expect(select).toMatchSnapshot();
  });

  it('should skip updating the default option if server time zone is not provided', async () => {
    document.documentElement.lang = 'ar';
    await setup(/* html */ `
      <select
        name="locale-current_time_zone"
        data-controller="w-init w-locale"
        data-action="w-init:ready->w-locale#localizeTimeZoneOptions"
      >
      </select>
    `);

    expect(select.getAttribute('data-controller')).toEqual('w-locale');
    const selected = select.selectedOptions[0];
    expect(selected).toBeTruthy();
    expect(selected.value).toEqual('');
    expect(selected.textContent).toEqual('Use server time zone');
    expect(select).toMatchSnapshot();
  });

  it('should allow updating the time zone options on an uncontrolled select element via events', async () => {
    document.documentElement.lang = 'id-ID';
    await setup(/* html */ `
      <form data-controller="w-locale">
        <select
          name="locale-current_time_zone"
          data-action="custom:event->w-locale#localizeTimeZoneOptions"
          data-w-locale-server-time-zone-param="Asia/Tokyo"
        >
        </select>
      </form>
    `);
    select.dispatchEvent(new CustomEvent('custom:event'));
    await Promise.resolve();

    expect(select.hasAttribute('data-controller')).toBe(false);
    const selected = select.selectedOptions[0];
    expect(selected).toBeTruthy();
    expect(selected.value).toEqual('');
    expect(selected.textContent).toEqual(
      'Use server time zone: Asia/Tokyo in id-ID with short format (Asia/Tokyo in id-ID with long format)',
    );
    expect(select).toMatchSnapshot();
  });

  it('should correctly apply French spacing rules to localized time zone labels', async () => {
    const gettextMock = jest.fn();
    gettextMock.mockImplementation(
      (str) => '%(time_zone_option)s : %(localized_time_zone_label)s',
    );
    window.django = { gettext: gettextMock };

    document.documentElement.lang = 'fr-FR';
    await setup(/* html */ `
      <select
        name="locale-current_time_zone"
        data-controller="w-init w-locale"
        data-action="w-init:ready->w-locale#localizeTimeZoneOptions"
        data-w-locale-server-time-zone-param="Europe/Paris"
      >
      </select>
    `);

    expect(select.getAttribute('data-controller')).toEqual('w-locale');
    expect(gettextMock).toHaveBeenCalledWith(
      '%(time_zone_option)s: %(localized_time_zone_label)s',
    );
    const selected = select.selectedOptions[0];
    expect(selected).toBeTruthy();
    expect(selected.value).toEqual('');
    expect(selected.textContent).toEqual(
      'Use server time zone : Europe/Paris in fr-FR with short format (Europe/Paris in fr-FR with long format)',
    );
    expect(select).toMatchSnapshot();
  });
});
