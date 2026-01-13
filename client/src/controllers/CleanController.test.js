import { Application } from '@hotwired/stimulus';
import { CleanController } from './CleanController';

import * as urlify from '../utils/urlify';
import * as wagtailConfig from '../config/wagtailConfig';

describe('CleanController', () => {
  let application;

  const eventNames = ['w-clean:applied'];

  const events = {};

  eventNames.forEach((name) => {
    document.addEventListener(name, (event) => {
      events[name].push(event);
    });
  });

  beforeEach(() => {
    eventNames.forEach((name) => {
      events[name] = [];
    });
  });

  describe('compare', () => {
    beforeEach(() => {
      application?.stop();

      document.body.innerHTML = `
      <input
        id="slug"
        name="slug"
        type="text"
        data-controller="w-clean"
      />`;

      application = Application.start();
      application.register('w-clean', CleanController);

      const input = document.getElementById('slug');

      input.dataset.action = [
        'blur->w-clean#urlify',
        'custom:event->w-clean#compare',
      ].join(' ');
    });

    it('should not prevent default if input has no value', async () => {
      const event = new CustomEvent('custom:event', {
        detail: { value: 'title alpha' },
      });

      event.preventDefault = jest.fn();

      document.getElementById('slug').dispatchEvent(event);

      await new Promise(process.nextTick);

      expect(document.getElementById('slug').value).toBe('');
      expect(event.preventDefault).not.toHaveBeenCalled();
    });

    it('should not prevent default if the values are the same', async () => {
      document.getElementById('slug').setAttribute('value', 'title-alpha');

      const event = new CustomEvent('custom:event', {
        detail: { value: 'title alpha' },
      });

      event.preventDefault = jest.fn();

      document.getElementById('slug').dispatchEvent(event);

      await new Promise(process.nextTick);

      expect(event.preventDefault).not.toHaveBeenCalled();
    });

    it('should prevent default using the slugify (default) behavior as the compare function when urlify values is not equal', async () => {
      const input = document.getElementById('slug');

      const title = 'Тестовий заголовок';

      input.setAttribute('value', title);

      // apply the urlify method to the content to ensure the value before check is urlify
      input.dispatchEvent(new Event('blur'));

      await new Promise(process.nextTick);

      expect(input.value).toEqual('testovij-zagolovok');

      const event = new CustomEvent('custom:event', {
        detail: { value: title },
      });

      event.preventDefault = jest.fn();

      input.dispatchEvent(event);

      await new Promise(process.nextTick);

      // slugify used for the compareAs value by default, so 'compare' fails
      expect(event.preventDefault).toHaveBeenCalled();
    });

    it('should not prevent default using the slugify (default) behavior as the compare function when urlify value is equal', async () => {
      const input = document.getElementById('slug');

      const title = 'the-french-dispatch-a-love-letter-to-journalists';

      input.setAttribute('value', title);

      // apply the urlify method to the content to ensure the value before check is urlify
      input.dispatchEvent(new Event('blur'));

      expect(input.value).toEqual(
        'the-french-dispatch-a-love-letter-to-journalists',
      );

      const event = new CustomEvent('custom:event', {
        detail: { value: title },
      });

      event.preventDefault = jest.fn();

      input.dispatchEvent(event);

      await new Promise(process.nextTick);

      // slugify used for the compareAs value by default, so 'compare' passes with the initial urlify value on blur
      expect(event.preventDefault).not.toHaveBeenCalled();
    });

    it('should not prevent default using the urlify behavior as the compare function when urlify value matches', async () => {
      const title = 'Тестовий заголовок';

      const input = document.getElementById('slug');

      input.setAttribute('data-w-clean-compare-as-param', 'urlify');
      input.setAttribute('value', title);

      // apply the urlify method to the content to ensure the value before check is urlify
      input.dispatchEvent(new Event('blur'));

      await new Promise(process.nextTick);

      expect(input.value).toEqual('testovij-zagolovok');

      const event = new CustomEvent('custom:event', {
        detail: { compareAs: 'urlify', value: title },
      });

      event.preventDefault = jest.fn();

      input.dispatchEvent(event);

      await new Promise(process.nextTick);

      expect(event.preventDefault).not.toHaveBeenCalled();
    });

    it('should prevent default if the values are not the same', async () => {
      document.getElementById('slug').setAttribute('value', 'title-alpha');

      const event = new CustomEvent('custom:event', {
        detail: { value: 'title beta' },
      });

      event.preventDefault = jest.fn();

      document.getElementById('slug').dispatchEvent(event);

      await new Promise(process.nextTick);

      expect(event.preventDefault).toHaveBeenCalled();
    });

    it('should not prevent default if both values are empty strings', async () => {
      const input = document.getElementById('slug');
      input.setAttribute('value', '');

      const event = new CustomEvent('custom:event', {
        detail: { value: '' },
      });

      event.preventDefault = jest.fn();

      input.dispatchEvent(event);

      await new Promise(process.nextTick);

      expect(event.preventDefault).not.toHaveBeenCalled();
    });

    it('should prevent default if the new value is an empty string but the existing value is not', async () => {
      const input = document.getElementById('slug');
      input.setAttribute('value', 'existing-value');

      const event = new CustomEvent('custom:event', {
        detail: { value: '' },
      });

      event.preventDefault = jest.fn();

      input.dispatchEvent(event);

      await new Promise(process.nextTick);

      expect(event.preventDefault).toHaveBeenCalled();
    });

    it('should allow the compare as identity to ensure that the values are always considered equal', async () => {
      expect(events['w-clean:applied']).toHaveLength(0);

      const input = document.getElementById('slug');
      input.setAttribute('data-w-clean-compare-as-param', 'identity');

      input.value = 'title-alpha';

      const event = new CustomEvent('custom:event', {
        detail: { value: 'title beta' },
      });

      event.preventDefault = jest.fn();

      input.dispatchEvent(event);

      await new Promise(process.nextTick);

      expect(event.preventDefault).not.toHaveBeenCalled();
      expect(events['w-clean:applied']).toHaveLength(1);
      expect(events['w-clean:applied']).toHaveProperty('0.detail', {
        action: 'identity',
        cleanValue: 'title-alpha',
        sourceValue: 'title-alpha',
      });

      // now use the compare from the event detail
      input.removeAttribute('data-w-clean-compare-as-param');

      input.value = 'title-delta';

      const event2 = new CustomEvent('custom:event', {
        detail: { value: 'title whatever', compareAs: 'identity' },
      });

      event2.preventDefault = jest.fn();

      input.dispatchEvent(event2);

      await new Promise(process.nextTick);

      expect(event2.preventDefault).not.toHaveBeenCalled();
      expect(events['w-clean:applied']).toHaveLength(2);
      expect(events['w-clean:applied']).toHaveProperty('1.detail', {
        action: 'identity',
        cleanValue: 'title-delta',
        sourceValue: 'title-delta',
      });
    });

    it('should correctly compare the formatted values', () => {
      const input = document.getElementById('slug');

      input.setAttribute(
        'data-w-clean-formatters-value',
        JSON.stringify([[/^(?!blog[-\s])/g.source, 'blog-']]),
      );

      // check that the formatter is applied (adds blog- to the start)
      input.value = 'blog-about-a-dog';
      const event = new CustomEvent('custom:event', {
        detail: { value: 'about a dog' },
      });
      event.preventDefault = jest.fn();

      input.dispatchEvent(event);

      expect(event.preventDefault).not.toHaveBeenCalled();

      // check the formatter runs on the compare for additional regex checks

      const event2 = new CustomEvent('custom:event', {
        detail: { value: 'blog about a dog' },
      });

      event2.preventDefault = jest.fn();

      input.dispatchEvent(event2);

      expect(event2.preventDefault).not.toHaveBeenCalled();

      // check when compare should return false

      const event3 = new CustomEvent('custom:event', {
        detail: { value: 'another blog about a dog' },
      });

      event3.preventDefault = jest.fn();

      input.dispatchEvent(event3);

      expect(event3.preventDefault).toHaveBeenCalled();
    });
  });

  describe('format', () => {
    beforeEach(() => {
      application?.stop();

      document.body.innerHTML = `
    <input
      id="id_slug"
      name="slug"
      type="text"
      data-controller="w-clean"
      data-action="blur->w-clean#format"
      data-w-clean-formatters-value='${JSON.stringify([[/\D/.source /* find all non-digits */]])}'

    />`;

      application = Application.start();
      application.register('w-clean', CleanController);
    });

    it('should format the input value with reasonable regex defaults', async () => {
      expect(events['w-clean:applied']).toHaveLength(0);

      const slugInput = document.getElementById('id_slug');
      slugInput.value = 'abc123def456ghi789jkl';

      slugInput.dispatchEvent(new Event('blur'));

      await new Promise(process.nextTick);

      expect(slugInput.value).toEqual('123456789');

      expect(events['w-clean:applied']).toHaveLength(1);
      expect(events['w-clean:applied']).toHaveProperty('0.detail', {
        action: 'format',
        cleanValue: '123456789',
        sourceValue: 'abc123def456ghi789jkl',
      });
    });

    it('should format the input value when focus is moved away from it (with trim)', async () => {
      expect(events['w-clean:applied']).toHaveLength(0);

      const slugInput = document.getElementById('id_slug');
      slugInput.setAttribute('data-w-clean-trim-value', 'true');
      slugInput.setAttribute(
        'data-w-clean-formatters-value',
        JSON.stringify([[/\B(?=(\d{3})+(?!\d))/.source, ',']]),
      );

      slugInput.value = ' 1234567890 ';

      slugInput.dispatchEvent(new Event('blur'));

      await new Promise(process.nextTick);

      expect(slugInput.value).toEqual('1,234,567,890');

      expect(events['w-clean:applied']).toHaveLength(1);
      expect(events['w-clean:applied']).toHaveProperty('0.detail', {
        action: 'format',
        cleanValue: '1,234,567,890',
        sourceValue: ' 1234567890 ',
      });
    });

    it('should support multiple formatters, using custom flags', async () => {
      const slugInput = document.getElementById('id_slug');

      /**
       * Example of position in word transliteration
       * @see https://czo.gov.ua/en/translit
       */
      slugInput.setAttribute(
        'data-w-clean-formatters-value',
        JSON.stringify([
          [/(?<=^|\s)Й/.source, 'Y'], // Й at the start of a word, case sensitive (default)
          [[/й/.source, 'i'], 'i'], // й elsewhere, case insensitive (custom, second param)
        ]),
      );

      slugInput.value = 'Йoc piй';

      slugInput.dispatchEvent(new Event('blur'));

      await new Promise(process.nextTick);

      expect(slugInput.value).toEqual('Yoc pii');
    });

    it('should ensure that formatters that are invalid are correctly flagged', async () => {
      /* eslint-disable no-console */
      expect(events['w-clean:applied']).toHaveLength(0);

      const slugInput = document.getElementById('id_slug');

      const consoleError = console.error;

      console.error = jest.fn();

      slugInput.setAttribute(
        'data-w-clean-formatters-value',
        JSON.stringify([['??:_INVALID']]),
      );

      await new Promise(process.nextTick);

      expect(console.error).toHaveBeenCalledTimes(1);

      const [, description, error, detail] = console.error.mock.calls[0];
      expect(description).toBe('Invalid regex pattern passed to formatters.');
      expect(error).toBeInstanceOf(SyntaxError);
      expect(detail).toEqual({ formatters: [['??:_INVALID']] });

      console.error = consoleError;

      expect(events['w-clean:applied']).toHaveLength(0);
      /* eslint-enable no-console */
    });
  });

  describe('slugify', () => {
    beforeEach(() => {
      application?.stop();

      document.body.innerHTML = `
    <input
      id="slug"
      name="slug"
      type="text"
      data-controller="w-clean"
      data-action="blur->w-clean#slugify"
    />`;

      application = Application.start();
      application.register('w-clean', CleanController);
    });

    it('should trim and slugify the input value when focus is moved away from it', async () => {
      expect(events['w-clean:applied']).toHaveLength(0);

      const input = document.getElementById('slug');
      input.value = '    slug  testing on     edit page ';

      input.dispatchEvent(new CustomEvent('blur'));

      await new Promise(process.nextTick);

      expect(document.getElementById('slug').value).toEqual(
        '-slug-testing-on-edit-page-', // non-trimmed adds dashes for all spaces (inc. end/start)
      );

      expect(events['w-clean:applied']).toHaveLength(1);
      expect(events['w-clean:applied']).toHaveProperty('0.detail', {
        action: 'slugify',
        cleanValue: '-slug-testing-on-edit-page-', // non-trimmed adds dashes for all spaces (inc. end/start)
        sourceValue: '    slug  testing on     edit page ',
      });
    });

    it('should slugify & trim (when enabled) the input value when focus is moved away from it', async () => {
      expect(events['w-clean:applied']).toHaveLength(0);

      const input = document.getElementById('slug');

      input.setAttribute('data-w-clean-trim-value', 'true'); // enable trimmed values

      input.value = '    slug  testing on     edit page ';

      input.dispatchEvent(new CustomEvent('blur'));

      await new Promise(process.nextTick);

      expect(document.getElementById('slug').value).toEqual(
        'slug-testing-on-edit-page',
      );

      expect(events['w-clean:applied']).toHaveLength(1);
      expect(events['w-clean:applied']).toHaveProperty('0.detail', {
        action: 'slugify',
        cleanValue: 'slug-testing-on-edit-page',
        sourceValue: '    slug  testing on     edit page ',
      });
    });

    it('should not allow unicode characters by default', async () => {
      const input = document.getElementById('slug');

      expect(
        input.hasAttribute('data-w-clean-allow-unicode-value'),
      ).toBeFalsy();

      input.value = 'Visiter Toulouse en été 2025';

      input.dispatchEvent(new CustomEvent('blur'));

      await new Promise(process.nextTick);

      expect(input.value).toEqual('visiter-toulouse-en-t-2025');
    });

    it('should allow unicode characters when allow-unicode-value is set to truthy', async () => {
      const input = document.getElementById('slug');
      input.setAttribute('data-w-clean-allow-unicode-value', 'true');

      expect(
        input.hasAttribute('data-w-clean-allow-unicode-value'),
      ).toBeTruthy();

      input.value = 'Visiter Toulouse en été 2025';

      input.dispatchEvent(new CustomEvent('blur'));

      await new Promise(process.nextTick);

      expect(input.value).toEqual('visiter-toulouse-en-été-2025');
    });
  });

  describe('urlify', () => {
    beforeEach(() => {
      application?.stop();

      document.body.innerHTML = `
      <input
        id="slug"
        name="slug"
        type="text"
        data-controller="w-clean"
      />`;

      application = Application.start();
      application.register('w-clean', CleanController);

      const input = document.getElementById('slug');

      input.dataset.action = [
        'blur->w-clean#slugify',
        'custom:event->w-clean#urlify:prevent',
      ].join(' ');
    });

    it('should update slug input value if the values are the same', async () => {
      expect(events['w-clean:applied']).toHaveLength(0);

      const input = document.getElementById('slug');
      input.value = 'urlify Testing On edit page  ';

      const event = new CustomEvent('custom:event', {
        detail: { value: 'urlify Testing On edit page' },
        bubbles: false,
      });

      document.getElementById('slug').dispatchEvent(event);

      await new Promise(process.nextTick);

      expect(input.value).toBe('urlify-testing-on-edit-page');

      expect(events['w-clean:applied']).toHaveLength(1);
      expect(events['w-clean:applied']).toHaveProperty('0.detail', {
        action: 'urlify',
        cleanValue: 'urlify-testing-on-edit-page',
        sourceValue: 'urlify Testing On edit page',
      });
    });

    it('should transform input with special (unicode) characters to their ASCII equivalent by default', async () => {
      const input = document.getElementById('slug');
      input.value = 'Some Title with éçà Spaces';

      const event = new CustomEvent('custom:event', {
        detail: { value: 'Some Title with éçà Spaces' },
      });

      document.getElementById('slug').dispatchEvent(event);

      await new Promise(process.nextTick);

      expect(input.value).toBe('some-title-with-eca-spaces');
    });

    it('should transform input with special (unicode) characters to keep unicode values if allow unicode value is truthy', async () => {
      const value = 'Dê-me fatias de   pizza de manhã --ou-- à noite';

      const input = document.getElementById('slug');
      input.setAttribute('data-w-clean-allow-unicode-value', 'true');

      input.value = value;

      const event = new CustomEvent('custom:event', { detail: { value } });

      document.getElementById('slug').dispatchEvent(event);

      await new Promise(process.nextTick);

      expect(input.value).toBe('dê-me-fatias-de-pizza-de-manhã-ou-à-noite');
    });

    it('should return an empty string when input contains only special characters', async () => {
      const input = document.getElementById('slug');
      input.value = '$$!@#$%^&*';

      const event = new CustomEvent('custom:event', {
        detail: { value: '$$!@#$%^&*' },
      });

      document.getElementById('slug').dispatchEvent(event);

      await new Promise(process.nextTick);

      expect(input.value).toBe('');
    });

    it('should trim the value, only if trim is enabled', async () => {
      const testValue = '  I féta eínai kalýteri .  ';

      const input = document.getElementById('slug');

      // the default behavior, with trim disabled
      input.value = testValue;

      input.dispatchEvent(new Event('blur'));
      await new Promise(process.nextTick);
      expect(input.value).toBe('-i-fta-enai-kalteri--');

      // after enabling trim
      input.setAttribute('data-w-clean-trim-value', 'true');
      input.value = testValue;

      input.dispatchEvent(new Event('blur'));
      await new Promise(process.nextTick);
      expect(input.value).toBe('i-fta-enai-kalteri-');

      // with unicode allowed & trim enabled
      input.setAttribute('data-w-clean-allow-unicode-value', 'true');
      input.value = testValue;

      input.dispatchEvent(new Event('blur'));
      await new Promise(process.nextTick);
      expect(input.value).toBe('i-féta-eínai-kalýteri-');
    });

    describe('urlify (with locale)', () => {
      let CleanController2;
      const originalActiveContentLocale =
        wagtailConfig.WAGTAIL_CONFIG.ACTIVE_CONTENT_LOCALE;
      let ACTIVE_CONTENT_LOCALE = originalActiveContentLocale;

      beforeAll(() => {
        jest.spyOn(urlify, 'urlify');

        Object.defineProperty(
          wagtailConfig.WAGTAIL_CONFIG,
          'ACTIVE_CONTENT_LOCALE',
          {
            get: () => ACTIVE_CONTENT_LOCALE,
            configurable: true,
          },
        );

        CleanController2 = require('./CleanController').CleanController;
      });

      const setup = async () => {
        application?.stop();

        document.body.innerHTML = `
        <input
          id="slug"
          name="slug"
          type="text"
          data-controller="w-clean"
          data-action="blur->w-clean#urlify"
          data-w-clean-trim-value="true"
        />`;

        application = Application.start();
        application.register('w-clean', CleanController2);

        await Promise.resolve();
      };

      afterEach(() => {
        jest.clearAllMocks();
      });

      afterAll(() => {
        jest.restoreAllMocks();
        Object.defineProperty(
          wagtailConfig.WAGTAIL_CONFIG,
          'ACTIVE_CONTENT_LOCALE',
          { value: originalActiveContentLocale, writable: true },
        );
      });

      const transliterationTest = ' Тестовий  Георгій  цехщик   заголовок  '; // ~Test George [shop]worker title
      const transliterationTestTrimmed =
        'Тестовий  Георгій  цехщик   заголовок'; // trimmed version (passed to events)
      const transliterationRu = 'testovij-georgij-cexshhik-zagolovok'; // Russian transliteration
      const transliterationUk = 'testovyi-heorhii-tsekhshchyk-zaholovok'; // Ukrainian transliteration

      it('should use the default locale when no locale is provided', async () => {
        expect(ACTIVE_CONTENT_LOCALE).toBe('en'); // default set in setup mocks

        await setup();

        const input = document.getElementById('slug');
        input.value = transliterationTest;

        input.dispatchEvent(new Event('blur'));

        await new Promise(process.nextTick);

        expect(urlify.urlify).toHaveBeenCalledTimes(1);
        expect(urlify.urlify).toHaveBeenCalledWith(transliterationTestTrimmed, {
          allowUnicode: false,
          locale: 'en',
        });

        expect(input.value).toBe(transliterationRu);
        expect(input.value).not.toBe(transliterationUk);
      });

      it('should use the the override locale when provided', async () => {
        ACTIVE_CONTENT_LOCALE = 'uk-UK';

        await setup();

        const input = document.getElementById('slug');
        input.value = transliterationTest;

        input.dispatchEvent(new Event('blur'));

        await new Promise(process.nextTick);

        expect(urlify.urlify).toHaveBeenCalledTimes(1);
        expect(urlify.urlify).toHaveBeenCalledWith(transliterationTestTrimmed, {
          allowUnicode: false,
          locale: 'uk-UK',
        });

        expect(input.value).toBe(transliterationUk);
        expect(input.value).not.toBe(transliterationRu);
      });

      it('should use an undetermined locale if no locale provided & not available from config or document', async () => {
        ACTIVE_CONTENT_LOCALE = undefined;

        await setup();

        const input = document.getElementById('slug');
        input.setAttribute('data-w-clean-allow-unicode-value', 'true');

        input.value = 'Тестовий заголовок';

        input.dispatchEvent(new Event('blur'));

        await new Promise(process.nextTick);

        expect(urlify.urlify).toHaveBeenCalledTimes(1);
        expect(urlify.urlify).toHaveBeenCalledWith('Тестовий заголовок', {
          allowUnicode: true,
          locale: 'und', // undetermined locale
        });

        expect(input.value).toBe('тестовий-заголовок'); // allows unicode in this test
      });
    });
  });
});
