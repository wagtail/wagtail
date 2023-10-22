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

  describe('the ability to support different data-rule attributes', () => {
    it('should support malformed matching and not error', async () => {
      await setup(`
    <form data-controller="w-rules" data-action="change->w-rules#resolve">
      <input type="text" name="title" value="bad" />
      <input type="text" name="subtitle" data-w-rules-target="enable" data-rule="{title:''}" />
      <div role="alert" data-w-rules-target="enable" data-rule="title=bad">
        Careful with this value.
      </div>
    </form>
      `);

      expect(
        Array.from(document.querySelectorAll('[data-w-rules-target]')).every(
          (target) => !target.disabled,
        ),
      ).toBe(true);

      expect(errors).toHaveLength(0);
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
        data-rule="${_([
          ['title', 'bad'],
          ['subtitle', ['bad']],
          ['agreement', ''],
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

    it('should treat false/null as a valid value to mean "empty" value as a string', async () => {
      await setup(`
    <form data-controller="w-rules" data-action="change->w-rules#resolve">
      <input id="confirm" type="checkbox" name="confirm" checked />
      <input
        class="test"
        type="text"
        name="a"
        data-w-rules-target="enable"
        data-rule='${_({ confirm: false })}' />
      <input
        class="test"
        type="text"
        name="b"
        data-w-rules-target="enable"
        data-rule="${_({ confirm: null })}" />
    </form>
      `);

      expect(
        Array.from(document.querySelectorAll('.test')).map(
          (target) => target.disabled,
        ),
      ).toEqual([true, true]);

      document.getElementById('confirm').checked = false;
      document
        .getElementById('confirm')
        .dispatchEvent(new CustomEvent('change', { bubbles: true }));

      await jest.runAllTimersAsync();

      expect(
        Array.from(document.querySelectorAll('.test')).map(
          (target) => target.disabled,
        ),
      ).toEqual([false, false]);
    });
  });

  describe('the ability for the controller to be activated or deactivated', () => {
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
    it('should provide a way to conditionally enable a target', async () => {
      await setup(`
    <form data-controller="w-rules" data-action="change->w-rules#resolve">
      <input type="checkbox" id="agreement-field" name="agreement">
      <button
        type="button"
        disabled
        data-w-rules-target="enable"
        data-rule="${_({ agreement: 'on' })}"
      >
        Continue
      </button>
    </form>`);

      const checkbox = document.querySelector('#agreement-field');
      const button = document.querySelector('[data-w-rules-target="enable"]');

      expect(checkbox.checked).toBe(false);
      expect(button.disabled).toBe(true);

      checkbox.click();
      await jest.runAllTimersAsync();

      expect(checkbox.checked).toBe(true);
      expect(button.disabled).toBe(false);

      checkbox.click();
      await jest.runAllTimersAsync();

      expect(checkbox.checked).toBe(false);
      expect(button.disabled).toBe(true);
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
        data-rule="${_({ remember: 'on' })}"
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
          data-rule="${_({
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
          data-rule="${_({
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
          data-rule="${_({ filter_method: ['fill'] })}"
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
