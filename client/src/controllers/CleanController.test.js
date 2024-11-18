import { Application } from '@hotwired/stimulus';
import { CleanController } from './CleanController';

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
  });
});
