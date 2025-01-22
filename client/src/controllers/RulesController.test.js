import { Application } from '@hotwired/stimulus';
import { RulesController } from './RulesController';
import { escapeHtml } from '../utils/text';

jest.useFakeTimers();

describe('RulesController', () => {
  const _ = (value) => escapeHtml(JSON.stringify(value));

  let application;
  let errors = [];

  const setup = async (html) => {
    document.body.innerHTML = `<main>${html}</main>`;

    application = Application.start();

    application.register('w-rules', RulesController);

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

  describe('the ability to parse different data-w-rules attributes', () => {
    it('should throw an error if the rule is malformed', async () => {
      expect(errors.length).toBe(0);

      await setup(`
        <form data-controller="w-rules" data-action="change->w-rules#resolve">
          <input type="text" name="title" value="bad" />
          <input type="text" name="subtitle" data-w-rules-target="enable" data-w-rules="{title:''}" />
          <div role="alert" data-w-rules-target="enable" data-w-rules="title=bad">
            Careful with this value.
          </div>
        </form>
          `);

      expect(
        Array.from(document.querySelectorAll('[data-w-rules-target]')).every(
          (target) => !target.disabled,
        ),
      ).toBe(true);

      expect(errors.length).toBeGreaterThan(1);

      expect(errors).toHaveProperty(
        '0.error.message',
        expect.stringContaining("Expected property name or '}' in JSON"),
      );
    });

    it('should gracefully handle different empty structures', async () => {
      await setup(`
      <form data-controller="w-rules" data-action="change->w-rules#resolve">
        <input name="a" type="text" data-w-rules-target="enable" data-w-rules="''" />
        <input name="a" type="text" data-w-rules-target="enable" data-w-rules="${_({})}" />
        <input name="b" type="text" data-w-rules-target="enable" data-w-rules="${_({ '': '' })}" />
        <input name="c" type="text" data-w-rules-target="enable" data-w-rules="${_([])}" />
        <input name="d" type="text" data-w-rules-target="enable" data-w-rules="${_([[]])}" />
      </form>`);

      document
        .querySelector('form')
        .dispatchEvent(new Event('change', { bubbles: true }));

      const handleEffect = jest.fn();
      document.addEventListener('w-rules:effect', handleEffect);

      expect(handleEffect).toHaveBeenCalledTimes(0);

      await jest.runAllTimersAsync();

      // check that no errors were thrown & no changes made due to empty-ish rules

      expect(
        [...document.querySelectorAll('input')].every(
          (input) => input.disabled,
        ),
      ).toBe(false);

      expect(handleEffect).toHaveBeenCalledTimes(0);
    });

    it('should support an entries style array of key/value pairs to be used as an object', async () => {
      await setup(`
    <form data-controller="w-rules" data-action="change->w-rules#resolve">
      <input type="text" name="title" value="bad" />
      <input type="text" name="subtitle" value="bad" />
      <input type="checkbox" name="agreement" id="agreement" checked />
      <textarea
        id="signature"
        data-w-rules-target="enable"
        data-w-rules="${_([
          ['title', 'bad'],
          ['subtitle', ['bad']],
          ['agreement', []],
        ])}"
        >
      </textarea>
    </form>
      `);

      expect(document.getElementById('signature').disabled).toBe(true);

      document.getElementById('agreement').checked = false;
      document
        .getElementById('agreement')
        .dispatchEvent(new CustomEvent('change', { bubbles: true }));

      await jest.runAllTimersAsync();

      expect(document.getElementById('signature').disabled).toBe(false);
    });

    it('should support checkboxes with an empty value', async () => {
      await setup(`
    <form data-controller="w-rules" data-action="change->w-rules#resolve">
      <input type="checkbox" name="agreement" value="" id="agreement" />
      <input
        id="enable-if-unchecked"
        data-w-rules-target="enable"
        data-w-rules="${_({ agreement: [] })}"
      />
      <input
        id="enable-if-checked"
        data-w-rules-target="enable"
        data-w-rules="${_({ agreement: [''] })}"
      />
    </form>
      `);

      expect(document.getElementById('enable-if-unchecked').disabled).toBe(
        false,
      );

      expect(document.getElementById('enable-if-checked').disabled).toBe(true);

      // check the agreement checkbox
      document.getElementById('agreement').checked = true;
      document
        .getElementById('agreement')
        .dispatchEvent(new CustomEvent('change', { bubbles: true }));

      await jest.runAllTimersAsync();

      expect(document.getElementById('enable-if-unchecked').disabled).toBe(
        true,
      );
      expect(document.getElementById('enable-if-checked').disabled).toBe(false);
    });

    it('should treat false/null as their string equivalents', async () => {
      // Note: We may revisit this in the future, for now we want to confirm all values are resolved to strings for consistency.

      await setup(`
    <form data-controller="w-rules" data-action="change->w-rules#resolve">
      <input id="confirm" type="checkbox" name="confirm" value="false" checked />
      <input id="signUp" type="text" name="signUp" value="null" />
      <input
        class="test"
        type="text"
        name="a"
        data-w-rules-target="enable"
        data-w-rules='${_({ confirm: false })}' />
      <input
        class="test"
        type="text"
        name="b"
        data-w-rules-target="enable"
        data-w-rules="${_({ signUp: null })}" />
    </form>
      `);

      // set to disabled when initializing based on rules
      expect(
        Array.from(document.querySelectorAll('.test')).map(
          (target) => target.disabled,
        ),
      ).toEqual([false, false]);

      document.getElementById('confirm').checked = false;
      document
        .getElementById('confirm')
        .dispatchEvent(new CustomEvent('change', { bubbles: true }));

      document.getElementById('signUp').value = '';
      document
        .getElementById('confirm')
        .dispatchEvent(new CustomEvent('change', { bubbles: true }));

      await jest.runAllTimersAsync();

      expect(
        Array.from(document.querySelectorAll('.test')).map(
          (target) => target.disabled,
        ),
      ).toEqual([true, true]);
    });

    it('should support multiple values for the same field name correctly', async () => {
      await setup(`
    <form data-controller="w-rules" data-action="change->w-rules#resolve">
      <fieldset>
        <legend>Choose your favorite starship</legend>

        <input type="checkbox" id="NCC-1701" name="starship" value="NCC-1701" />
        <label for=""NCC-1701">Enterprise</label><br />

        <input type="checkbox" id="NCC-1701-D" name="starship" value="NCC-1701-D" />
        <label for="NCC-1701-D">Enterprise D</label><br />

        <input type="checkbox" id="NCC-1701-E" name="starship" value="NCC-1701-E" />
        <label for="NCC-1701-E">Enterprise E</label>

        <input type="checkbox" id="NCC-71201" name="starship" value="NCC-71201" />
        <label for="NCC-71201">Prometheus</label>
      </fieldset>
      <input
        id="continue"
        type="button"
        name="continue"
        data-w-rules-target="enable"
        data-w-rules="${_({ starship: ['NCC-1701-D', 'NCC-1701-E'] })}" />
    </form>
      `);

      // set to disabled when initializing based on rules
      expect(document.getElementById('continue').disabled).toBe(true);

      // 1 - Check rule against a value that is not in the enable rules

      document.getElementById('NCC-1701').checked = true;
      document
        .getElementById('NCC-1701')
        .dispatchEvent(new CustomEvent('change', { bubbles: true }));

      document.getElementById('NCC-71201').checked = true;
      document
        .getElementById('NCC-71201')
        .dispatchEvent(new CustomEvent('change', { bubbles: true }));

      await jest.runAllTimersAsync();

      expect(document.getElementById('continue').disabled).toBe(true);

      // 2 - Check rule against values that are in the the enable rules

      document.getElementById('NCC-1701').checked = false;
      document
        .getElementById('NCC-1701')
        .dispatchEvent(new CustomEvent('change', { bubbles: true }));

      document.getElementById('NCC-1701-D').checked = true;
      document
        .getElementById('NCC-1701-D')
        .dispatchEvent(new CustomEvent('change', { bubbles: true }));

      document.getElementById('NCC-1701-E').checked = true;
      document
        .getElementById('NCC-1701-E')
        .dispatchEvent(new CustomEvent('change', { bubbles: true }));

      await jest.runAllTimersAsync();

      expect(document.getElementById('continue').disabled).toBe(false);
    });
  });

  describe('the ability to find the most suitable form for formData', () => {
    it('should resolve the form from the controlled element input if the form is not the controlled element', async () => {
      await setup(`
      <form>
        <input type="text" name="title" value="bad" />
        <input
          name="enter"
          type="text"
          data-controller="w-rules"
          data-action="change@document->w-rules#resolve"
          data-w-rules-target="enable"
          data-w-rules="${_([['title', 'good']])}"
        >
      </form>`);

      const input = document.querySelector('input[name="title"]');
      const enableInput = document.querySelector('input[name="enter"]');

      expect(enableInput.disabled).toBeTruthy();

      input.value = 'good';
      input.dispatchEvent(new Event('change', { bubbles: true }));
      await jest.runAllTimersAsync();

      expect(enableInput.disabled).toBeFalsy();
    });

    it('should resolve the form from the controlled element closest form if it cannot find it on the controlled element', async () => {
      await setup(`
      <form>
        <input type="text" name="title" value="bad" />
        <div data-controller="w-rules" data-action="change@document->w-rules#resolve">
          <input name="enter" type="text" data-w-rules-target="enable" data-w-rules="${_([['title', 'good']])}" >
        </div>
      </form>`);

      const input = document.querySelector('input[name="title"]');
      const enableInput = document.querySelector('input[name="enter"]');

      expect(enableInput.disabled).toBeTruthy();

      input.value = 'good';
      input.dispatchEvent(new Event('change', { bubbles: true }));
      await jest.runAllTimersAsync();

      expect(enableInput.disabled).toBeFalsy();
    });
  });

  describe('the ability for the controller to avoid unnecessary resolving', () => {
    it('should not check for the form data if there are no targets', async () => {
      const handleResolved = jest.fn();

      document.addEventListener('w-rules:resolved', handleResolved);

      await setup(`
    <form data-controller="w-rules" data-action="change->w-rules#resolve">
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

      noteField.setAttribute('data-w-rules-target', 'enable');
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

  describe('conditionally enabling a target', () => {
    it('should provide a way to conditionally enable a target and dispatch events', async () => {
      const handleResolved = jest.fn();
      const handleEffect = jest.fn();

      document.addEventListener('w-rules:effect', handleEffect);
      document.addEventListener('w-rules:resolved', handleResolved);

      await setup(`
    <form data-controller="w-rules" data-action="change->w-rules#resolve">
      <input type="checkbox" id="agreement-field" name="agreement">
      <button
        id="continue"
        type="button"
        disabled
        data-w-rules-target="enable"
        data-w-rules="${_({ agreement: 'on' })}"
      >
        Continue
      </button>
    </form>`);

      const checkbox = document.querySelector('#agreement-field');
      const button = document.querySelector('[data-w-rules-target="enable"]');

      expect(checkbox.checked).toBe(false);
      expect(button.disabled).toBe(true);
      expect(handleResolved).toHaveBeenCalledTimes(1);
      expect(handleEffect).toHaveBeenCalledTimes(0); // no changes actually made to elements

      checkbox.click();
      checkbox.dispatchEvent(
        new Event('change', { bubbles: true, cancelable: false }),
      );
      await jest.runAllTimersAsync();

      expect(checkbox.checked).toBe(true);
      expect(button.disabled).toBe(false);

      checkbox.click();
      checkbox.dispatchEvent(
        new Event('change', { bubbles: true, cancelable: false }),
      );
      await jest.runAllTimersAsync();

      expect(checkbox.checked).toBe(false);
      expect(button.disabled).toBe(true);
      expect(handleResolved).toHaveBeenCalledTimes(3); // rules are resolved two additional times
      expect(handleEffect).toHaveBeenCalledTimes(2); // two changes made to elements
      expect(handleEffect.mock.calls[0][0]).toEqual(
        expect.objectContaining({
          target: document.getElementById('continue'),
          detail: {
            effect: 'enable',
            enable: true,
          },
        }),
      );
      expect(handleEffect.mock.calls[1][0]).toEqual(
        expect.objectContaining({
          target: document.getElementById('continue'),
          detail: {
            effect: 'enable',
            enable: false,
          },
        }),
      );
    });

    it('should ensure that the enabled/disabled attributes sync once connected', async () => {
      await setup(`
    <form id="form" data-controller="w-rules">
      <fieldset>
        <input type="password" name="password" />
        <input type="email" name="email" />
        <input type="checkbox" name="remember" />
      </fieldset>
      <label for="">This is my device.</label>
      <input
        type="checkbox"
        id="my-device-check"
        name="my-device"
        data-w-rules-target="enable"
        data-w-rules="${_({ remember: 'on' })}"
      />
    </form>`);

      expect(document.getElementById('my-device-check').disabled).toBe(true);
    });

    it('should support conditional enabling of sets of fields based on a select field', async () => {
      await setup(`
    <form class="w-mb-10" data-controller="w-rules" data-action="change->w-rules#resolve">
      <select name="filter_method" id="id_filter_method" value="original">
        <option value="original">Original size</option>
        <option value="width">Resize to width</option>
        <option value="height">Resize to height</option>
        <option value="min">Resize to min</option>
        <option value="max">Resize to max</option>
        <option value="fill">Resize to fill</option>
      </select>
      <fieldset>
        <input
          type="number"
          name="width"
          value="150"
          id="id_width"
          disabled
          data-w-rules-target="enable"
          data-w-rules="${_({
            filter_method: ['fill', 'max', 'min', 'width'],
          })}"
        />
        <input
          type="number"
          name="height"
          value="162"
          id="id_height"
          disabled
          data-w-rules-target="enable"
          data-w-rules="${_({
            filter_method: ['fill', 'height', 'max', 'min'],
          })}"
        />
        <input
          type="number"
          name="closeness"
          value="0"
          id="id_closeness"
          disabled
          data-w-rules-target="enable"
          data-w-rules="${_({ filter_method: ['fill'] })}"
        />
      </fieldset>
    </form>
      `);

      const filterField = document.getElementById('id_filter_method');
      const widthField = document.getElementById('id_width');
      const heightField = document.getElementById('id_height');
      const closenessField = document.getElementById('id_closeness');

      expect(filterField.value).toEqual('original');

      // should all be disabled at the start (original selected)

      expect(widthField.disabled).toBe(true);
      expect(heightField.disabled).toBe(true);
      expect(closenessField.disabled).toBe(true);

      // now change the filter to width

      filterField.value = 'width';

      filterField.dispatchEvent(new Event('change', { bubbles: true }));
      await jest.runAllTimersAsync();

      expect(widthField.disabled).toBe(false);
      expect(heightField.disabled).toBe(true);
      expect(closenessField.disabled).toBe(true);

      // now change the filter to height

      filterField.value = 'height';

      filterField.dispatchEvent(new Event('change', { bubbles: true }));
      await jest.runAllTimersAsync();

      expect(widthField.disabled).toBe(true);
      expect(heightField.disabled).toBe(false);
      expect(closenessField.disabled).toBe(true);

      // now change the filter to max

      filterField.value = 'max';

      filterField.dispatchEvent(new Event('change', { bubbles: true }));
      await jest.runAllTimersAsync();

      expect(widthField.disabled).toBe(false);
      expect(heightField.disabled).toBe(false);
      expect(closenessField.disabled).toBe(true);

      // now change the filter to fill

      filterField.value = 'fill';

      filterField.dispatchEvent(new Event('change', { bubbles: true }));
      await jest.runAllTimersAsync();

      expect(widthField.disabled).toBe(false);
      expect(heightField.disabled).toBe(false);
      expect(closenessField.disabled).toBe(false);

      // set back to original

      filterField.value = 'original';

      filterField.dispatchEvent(new Event('change', { bubbles: true }));
      await jest.runAllTimersAsync();

      expect(filterField.value).toEqual('original');
      expect(widthField.disabled).toBe(true);
      expect(heightField.disabled).toBe(true);
      expect(closenessField.disabled).toBe(true);
    });
  });
});
