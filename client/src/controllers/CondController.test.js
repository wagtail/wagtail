import { Application } from '@hotwired/stimulus';
import { CondController } from './CondController';
import { escapeHtml } from '../utils/text';

jest.useFakeTimers();

describe('CondController', () => {
  const _ = (value) => escapeHtml(JSON.stringify(value));

  let application;
  let errors = [];

  const setup = async (html) => {
    document.body.innerHTML = `<main>${html}</main>`;

    application = Application.start();
    application.register('w-cond', CondController);

    application.handleError = (error, message) => {
      errors.push({ error, message });
    };

    await jest.runAllTimersAsync();
  };

  afterEach(() => {
    application?.stop();
    jest.clearAllMocks();
    errors = [];
  });

  describe('the ability to support different data-match attributes', () => {
    it('should support malformed matching and not error', async () => {
      await setup(`
    <form data-controller="w-cond" data-action="change->w-cond#resolve">
      <input type="text" name="title" value="bad" />
      <input type="text" name="subtitle" data-w-cond-target="show" data-match="{title:''}" />
      <div role="alert" data-w-cond-target="show" data-match="title=bad">
        Careful with this value.
      </div>
    </form>
      `);

      expect(
        Array.from(document.querySelectorAll('[data-w-cond-target]')).every(
          (target) => !target.hidden,
        ),
      ).toBe(true);

      expect(errors).toHaveLength(0);
    });

    it('should support an entries style array of key/value pairs to be used as an object', async () => {
      await setup(`
    <form data-controller="w-cond" data-action="change->w-cond#resolve">
      <input type="text" name="title" value="bad" />
      <input type="text" name="subtitle" value="bad" />
      <input type="checkbox" name="agreement" id="agreement" checked />
      <div
        id="alert"
        role="alert"
        data-w-cond-target="show"
        data-match="${_([
          ['title', 'bad'],
          ['subtitle', ['bad']],
          ['agreement', ''],
        ])}"
        >
        Use better titles & subtitles & ensure the agreement is checked.
      </div>
    </form>
      `);

      expect(document.getElementById('alert').hidden).toBe(true);

      document.getElementById('agreement').checked = false;
      document
        .getElementById('agreement')
        .dispatchEvent(new CustomEvent('change', { bubbles: true }));

      await jest.runAllTimersAsync();

      expect(document.getElementById('alert').hidden).toBe(false);
    });

    it('should treat false/null as a valid value to mean "empty" value as a string', async () => {
      await setup(`
    <form data-controller="w-cond" data-action="change->w-cond#resolve">
      <input id="confirm" type="checkbox" name="confirm" checked />
      <input
        class="test"
        type="text"
        name="a"
        data-w-cond-target="show"
        data-match='${_({ confirm: false })}' />
      <input
        class="test"
        type="text"
        name="b"
        data-w-cond-target="show"
        data-match="${_({ confirm: null })}" />
    </form>
      `);

      expect(
        Array.from(document.querySelectorAll('.test')).map(
          (target) => target.hidden,
        ),
      ).toEqual([true, true]);

      document.getElementById('confirm').checked = false;
      document
        .getElementById('confirm')
        .dispatchEvent(new CustomEvent('change', { bubbles: true }));

      await jest.runAllTimersAsync();

      expect(
        Array.from(document.querySelectorAll('.test')).map(
          (target) => target.hidden,
        ),
      ).toEqual([false, false]);
    });
  });

  describe('the ability for the controller to be activated or deactivated', () => {
    it('should not check for the form data if there are no targets', async () => {
      const handleResolved = jest.fn();

      document.addEventListener('w-cond:resolved', handleResolved);

      await setup(`
    <form data-controller="w-cond" data-action="change->w-cond#resolve">
      <input type="checkbox" name="ignored" />
      <input type="text" id="note" name="note" />
    </form>`);

      const noteField = document.getElementById('note');

      expect(
        document.querySelector('form').getAttribute('data-controller'),
      ).toBeTruthy();

      expect(handleResolved).not.toHaveBeenCalled();

      document
        .querySelector('input')
        .dispatchEvent(new Event('change', { bubbles: true }));
      await jest.runAllTimersAsync();

      expect(handleResolved).not.toHaveBeenCalled();

      // add a target & trigger a change event

      noteField.setAttribute('data-w-cond-target', 'show');
      await jest.runAllTimersAsync();

      expect(handleResolved).toHaveBeenCalledTimes(1);

      noteField.dispatchEvent(new Event('change', { bubbles: true }));
      await jest.runAllTimersAsync();

      expect(handleResolved).toHaveBeenCalledTimes(2);

      // now remove the target and check that the event no longer fires

      noteField.remove();

      document
        .querySelector('input')
        .dispatchEvent(new Event('change', { bubbles: true }));

      await jest.runAllTimersAsync();

      expect(handleResolved).toHaveBeenCalledTimes(2);
    });
  });

  describe('conditionally showing a target', () => {
    it('should provide a way to conditionally show a target', async () => {
      await setup(`
    <form id="form" data-controller="w-cond" data-action="change->w-cond#resolve">
      <div
        id="alert"
        data-w-cond-target="show"
        data-match="${_({ email: '' })}"
      >
        Please enter your email before continuing.
      </div>
      <input type="email" id="email-field" name="email" />
      <input type="text" id="name-field" name="name" />
    </form>`);

      const nameField = document.getElementById('name-field');
      const emailField = document.getElementById('email-field');

      const alert = document.getElementById('alert');
      expect(alert.hidden).toBe(false);

      // add a non-empty email value
      emailField.value = 'joe@email.co';

      emailField.dispatchEvent(new Event('change', { bubbles: true }));
      await jest.runAllTimersAsync();

      expect(alert.hidden).toBe(true);

      // reset the value to empty
      emailField.value = '';

      emailField.dispatchEvent(new Event('change', { bubbles: true }));
      await jest.runAllTimersAsync();

      expect(alert.hidden).toBe(false);
    });

    it('should ensure that the hidden attribute will be synced with the desired match once connected', async () => {
      await setup(`
    <form id="form" data-controller="w-cond">
      <fieldset>
        <input type="password" name="password" />
        <input type="email" name="email" />
        <input type="checkbox" name="remember" id="remember-me-field" />
      </fieldset>
      <label for="">This is my device.</label>
      <div
        id="alert"
        data-w-cond-target="show"
        data-match="${_({ remember: 'on' })}"
      >
        Cookies will be saved to this device.
      </div>
      <button type="button">Continue</button>
    </form>`);

      // The checkbox is not checked, #alert is also not set with hidden (in supplied DOM)
      // Should update once connected
      expect(document.getElementById('alert').hidden).toBe(true);
    });

    describe('using as a filtered-select', () => {
      beforeEach(async () => {
        await setup(`
  <form
    data-controller="w-cond"
    data-action="change->w-cond#resolve"
  >
    <label for="continent-field">Continent</label>
    <select id="continent-field" name="continent">
      <option value="">--------</option>
      <option value="1">Europe</option>
      <option value="2">Africa</option>
      <option value="3">Asia</option>
    </select>
    <label for="country-field">Country</label>
    <select id="country-field" name="country">
      <option value="">--------</option>
      <option
        value="1"
        data-w-cond-target="show"
        data-match='${_({ continent: ['', 3] })}'
      >
        China
      </option>
      <option
        value="2"
        data-w-cond-target="show"
        data-match='${_({ continent: ['', 2] })}'
      >
        Egypt
      </option>
      <option
        value="3"
        data-w-cond-target="show"
        data-match='${_({ continent: ['', 1] })}'
      >
        France
      </option>
      <option
        value="4"
        data-w-cond-target="show"
        data-match='${_({ continent: ['', 1] })}'
      >
        Germany
      </option>
      <option
        value="5"
        data-w-cond-target="show"
        data-match='${_({ continent: ['', 3] })}'
      >
        Japan
      </option>
      <option
        value="6"
        data-w-cond-target="show"
        data-match='${_({ continent: ['', 1, 3] })}'
      >
        Russia
      </option>
      <option
        value="7"
        data-w-cond-target="show"
        data-match='${_({ continent: ['', 2] })}'
      >
        South
       Africa</option>
      <option
        value="8"
        data-w-cond-target="show"
        data-match='${_({ continent: ['', 1, 3] })}'
      >
        Turkey
      </option>
    </select>
  </form>`);
      });

      const getShownOptions = () =>
        Array.from(document.getElementById('country-field').options)
          .filter((option) => !option.hidden)
          .map((option) => option.value);

      const allOptions = ['', '1', '2', '3', '4', '5', '6', '7', '8'];

      it('it should show all options by default', async () => {
        expect(getShownOptions()).toEqual(allOptions);
      });

      it('it should hide some options based on the selection within another field', async () => {
        const continentField = document.getElementById('continent-field');

        expect(getShownOptions()).toEqual(allOptions);

        continentField.value = '2'; // Africa

        continentField.dispatchEvent(new Event('change', { bubbles: true }));
        await jest.runAllTimersAsync();

        expect(getShownOptions()).toEqual(['', '2', '7']);

        continentField.value = 1; // Europe - intentionally using int

        continentField.dispatchEvent(new Event('change', { bubbles: true }));
        await jest.runAllTimersAsync();

        expect(getShownOptions()).toEqual(['', '3', '4', '6', '8']);

        continentField.value = ''; // clear selection

        continentField.dispatchEvent(new Event('change', { bubbles: true }));
        await jest.runAllTimersAsync();

        expect(getShownOptions()).toEqual(allOptions);
      });

      it('should clear a selected option if it is being hidden/disabled', async () => {
        const continentField = document.getElementById('continent-field');
        const countryField = document.getElementById('country-field');

        expect(getShownOptions()).toEqual(allOptions);

        countryField.value = '8'; // Turkey
        countryField.dispatchEvent(new Event('change', { bubbles: true }));

        await jest.runAllTimersAsync();

        expect(countryField.value).toEqual('8');

        // now change the continent to an incompatible value (Africa)
        continentField.value = '2'; // Africa

        continentField.dispatchEvent(new Event('change', { bubbles: true }));
        await jest.runAllTimersAsync();

        expect(getShownOptions()).toEqual(['', '2', '7']);
        expect(countryField.value).toEqual('');
      });
    });
  });
});
