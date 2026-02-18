import { Application } from '@hotwired/stimulus';
import { RulesController } from './RulesController';
import { escapeHtml } from '../utils/text';

jest.useFakeTimers();

describe('RulesController', () => {
  const _ = (value) => escapeHtml(JSON.stringify(value));

  let application;
  let errors = [];

  const eventNames = ['change', 'w-rules:effect', 'w-rules:resolved'];

  const events = {};
  const eventListeners = {};

  const setup = async (html) => {
    document.body.innerHTML = `<main>${html}</main>`;

    application = Application.start();

    application.register('w-rules', RulesController);

    application.handleError = (error, message) => {
      errors.push({ error, message });
    };

    await jest.runAllTimersAsync();
  };

  beforeAll(() => {
    eventNames.forEach((name) => {
      events[name] = [];
    });

    Object.keys(events).forEach((name) => {
      const eventListener = jest.fn((event) => {
        events[name].push(event);
      });

      document.addEventListener(name, eventListener);

      eventListeners[name] = eventListener;
    });
  });

  afterEach(() => {
    application?.stop();
    jest.clearAllMocks();
    errors = [];

    eventNames.forEach((name) => {
      eventListeners[name].mockClear();
      events[name] = [];
    });
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
      expect(errors).toHaveProperty(
        '1.message',
        expect.stringContaining(
          "Unable to parse rule at the attribute 'data-w-rules'",
        ),
      );
    });

    it('should throw an error if an invalid match value is provided as the controller value', async () => {
      expect(errors.length).toBe(0);

      await setup(`
      <form data-controller="w-rules" data-action="change->w-rules#resolve" data-w-rules-match-value="_INVALID_">
        <input type="text" name="title" value="bad" />
        <input type="text" name="subtitle" data-w-rules-target="enable" data-w-rules='{"title":""}' />
      </form>`);

      expect(errors.length).toEqual(1);

      const [{ error, message }] = errors;

      expect(error).toHaveProperty(
        'message',
        "Invalid match value: '_INVALID_'.",
      );

      expect(message).toEqual(
        "Error Match value must be one of: 'all', 'any', 'not', 'one'.",
      );
    });

    it('should throw an error if an invalid match value is provided in the action params value', async () => {
      expect(errors.length).toBe(0);

      await setup(`
      <form data-controller="w-rules" data-action="change->w-rules#resolve" data-w-rules-match-param="_INVALID_">
        <input type="text" name="title" value="bad" />
        <input type="text" name="subtitle" data-w-rules-target="enable" data-w-rules='{"title":""}' />
      </form>`);

      // does not trigger on connect as event was not used
      expect(errors.length).toEqual(0);

      // dispatch event to use params
      document
        .querySelector('input[name="title"]')
        .dispatchEvent(new Event('change', { bubbles: true }));

      await jest.runAllTimersAsync();

      expect(errors.length).toEqual(1);

      const [{ error, message }] = errors;

      expect(error).toHaveProperty(
        'message',
        "Invalid match value: '_INVALID_'.",
      );

      expect(message).toEqual(
        "Error Match value must be one of: 'all', 'any', 'not', 'one'.",
      );
    });

    it('should throw an error if an invalid match value is provided as the target attributes', async () => {
      expect(errors.length).toBe(0);

      await setup(`
      <form data-controller="w-rules" data-action="change->w-rules#resolve">
        <input type="text" name="title" value="bad" />
        <input type="text" name="subtitle" data-w-rules-target="enable" data-w-rules='{"title":""}' data-w-rules-match="_INVALID_" />
      </form>`);

      expect(errors.length).toEqual(1);

      const [{ error, message }] = errors;

      expect(error).toHaveProperty(
        'message',
        "Invalid match value: '_INVALID_'.",
      );

      expect(message).toEqual(
        "Error Match value must be one of: 'all', 'any', 'not', 'one'.",
      );
    });

    it('should throw an error if an invalid match value is provided as the specific target attributes', async () => {
      expect(errors.length).toBe(0);

      await setup(`
      <form data-controller="w-rules" data-action="change->w-rules#resolve">
        <input type="text" name="title" value="bad" />
        <input type="text" name="subtitle" data-w-rules-target="enable" data-w-rules='{"title":""}' data-w-rules-enable-match="_INVALID_" />
      </form>`);

      expect(errors.length).toEqual(1);

      const [{ error, message }] = errors;

      expect(error).toHaveProperty(
        'message',
        "Invalid match value: '_INVALID_'.",
      );

      expect(message).toEqual(
        "Error Match value must be one of: 'all', 'any', 'not', 'one'.",
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

      expect(eventListeners['w-rules:effect']).toHaveBeenCalledTimes(0);

      await jest.runAllTimersAsync();

      // check that no errors were thrown & no changes made due to empty-ish rules

      expect(
        [...document.querySelectorAll('input')].every(
          (input) => input.disabled,
        ),
      ).toBe(false);

      expect(eventListeners['w-rules:effect']).toHaveBeenCalledTimes(0);
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

    it('should attempt to read the specific attribute for the effect if found', async () => {
      await setup(`
    <form data-controller="w-rules" data-action="change->w-rules#resolve">
      <input type="text" name="title" value="bad" />
      <input type="text" name="subtitle" value="good" />
      <textarea
        id="signature"
        data-w-rules-target="enable"
        data-w-rules="${_({ title: 'good' } /* should be ignored */)}"
        data-w-rules-enable="${_({ subtitle: 'good' })}"
        >
      </textarea>
    </form>
    `);

      const signature = document.getElementById('signature');
      const subtitle = document.querySelector('[name="subtitle"]');

      expect(signature.disabled).toBe(false);

      subtitle.value = 'bad';
      subtitle.dispatchEvent(new CustomEvent('change', { bubbles: true }));

      await jest.runAllTimersAsync();

      expect(signature.disabled).toBe(true);
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
      await setup(`
    <form data-controller="w-rules" data-action="change->w-rules#resolve">
      <input type="checkbox" name="ignored" />
      <input type="text" id="note" name="note" />
    </form>`);

      const noteField = document.getElementById('note');

      expect(
        document.querySelector('form').getAttribute('data-controller'),
      ).toBeTruthy();

      expect(eventListeners['w-rules:resolved']).not.toHaveBeenCalled();

      document
        .querySelector('input')
        .dispatchEvent(new Event('change', { bubbles: true }));
      await jest.runAllTimersAsync();

      expect(eventListeners['w-rules:resolved']).not.toHaveBeenCalled();

      // add a target & trigger a change event

      noteField.setAttribute('data-w-rules-target', 'enable');
      await jest.runAllTimersAsync();

      expect(eventListeners['w-rules:resolved']).toHaveBeenCalledTimes(1);

      noteField.dispatchEvent(new Event('change', { bubbles: true }));
      await jest.runAllTimersAsync();

      expect(eventListeners['w-rules:resolved']).toHaveBeenCalledTimes(2);

      // now remove the target and check that the event no longer fires

      noteField.remove();

      document
        .querySelector('input')
        .dispatchEvent(new Event('change', { bubbles: true }));

      await jest.runAllTimersAsync();

      expect(eventListeners['w-rules:resolved']).toHaveBeenCalledTimes(2);
    });
  });

  describe('conditionally enabling a target', () => {
    it('should provide a way to conditionally enable a target and dispatch events', async () => {
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
      expect(eventListeners['w-rules:resolved']).toHaveBeenCalledTimes(1);
      expect(eventListeners['w-rules:effect']).toHaveBeenCalledTimes(0); // no changes actually made to elements

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
      expect(eventListeners['w-rules:resolved']).toHaveBeenCalledTimes(3); // rules are resolved two additional times
      expect(eventListeners['w-rules:effect']).toHaveBeenCalledTimes(2); // two changes made to elements
      expect(eventListeners['w-rules:effect'].mock.calls[0][0]).toEqual(
        expect.objectContaining({
          target: document.getElementById('continue'),
          detail: {
            effect: 'enable',
            enable: true,
          },
        }),
      );
      expect(eventListeners['w-rules:effect'].mock.calls[1][0]).toEqual(
        expect.objectContaining({
          target: document.getElementById('continue'),
          detail: {
            effect: 'enable',
            enable: false,
          },
        }),
      );
    });

    it('should support the ability to stop the effect from being applied by preventing the effect event', async () => {
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

      const button = document.getElementById('continue');
      const checkbox = document.getElementById('agreement-field');

      expect(button.disabled).toBe(true);
      expect(eventListeners['w-rules:effect']).toHaveBeenCalledTimes(0);

      // prevent the effect event the first time it's dispatched

      eventListeners['w-rules:effect'].mockImplementationOnce((event) => {
        event.preventDefault();
      });

      // update the checkbox & dispatch change

      checkbox.click();
      checkbox.dispatchEvent(
        new Event('change', { bubbles: true, cancelable: false }),
      );

      await jest.runAllTimersAsync();

      expect(eventListeners['w-rules:effect']).toHaveBeenCalledTimes(1);

      // check that the button is still disabled
      expect(button.disabled).toBe(true);

      // trigger the effect a second time
      checkbox.dispatchEvent(
        new Event('change', { bubbles: true, cancelable: false }),
      );
      await jest.runAllTimersAsync();

      // assert that the event was dispatched and this time the effect has not been prevented
      expect(eventListeners['w-rules:effect']).toHaveBeenCalledTimes(2);

      expect(button.disabled).toBe(false);
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

    describe('using different match values', () => {
      it('should support the ability to to trigger an effect if any (not all) field rule matches', async () => {
        await setup(`
      <form data-controller="w-rules" data-action="change->w-rules#resolve" data-w-rules-match-value="any">
        <fieldset>
          <legend>Enter the registration number or opt to create a new number to continue.</legend>
          <input id="number" name="number" type="text" />
          <input id="create" name="create" type="checkbox" />
        </fieldset>
        <input
          id="continue"
          type="button"
          name="continue"
          data-w-rules-target="enable"
          data-w-rules-enable="${_({ create: ['on'], number: ['1701', '74656', '74913'] })}" />
      </form>`);

        const numberField = document.getElementById('number');
        const createField = document.getElementById('create');
        const continueButton = document.getElementById('continue');

        expect(continueButton.disabled).toBe(true); // disabled by default

        numberField.value = '1701';
        numberField.dispatchEvent(new Event('change', { bubbles: true }));

        await jest.runAllTimersAsync();

        expect(continueButton.disabled).toBe(false);

        numberField.value = '99999';
        createField.checked = true;

        numberField.dispatchEvent(new Event('change', { bubbles: true }));

        await jest.runAllTimersAsync();

        expect(continueButton.disabled).toBe(false);

        createField.checked = false;

        numberField.dispatchEvent(new Event('change', { bubbles: true }));

        await jest.runAllTimersAsync();

        expect(continueButton.disabled).toBe(true);
      });

      it('should support the ability to match one field rule', async () => {
        await setup(`
      <form data-controller="w-rules" data-action="change->w-rules#resolve" data-w-rules-match-value="one">
        <fieldset>
          <legend>Enter the registration number or opt to create a new number to continue.</legend>
          <input id="number" name="number" type="text" />
          <input id="create" name="create" type="checkbox" checked />
        </fieldset>
        <input
          id="continue"
          type="button"
          name="continue"
          data-w-rules-target="enable"
          data-w-rules-enable="${_({ create: ['on'], number: ['1701', '74656', '74913'] })}" />
      </form>`);

        const numberField = document.getElementById('number');
        const createField = document.getElementById('create');
        const continueButton = document.getElementById('continue');

        // it should have the input enabled by default as there is one passing match (checkbox checked)
        expect(continueButton.disabled).toBe(false);

        // set the number field value to something that matches, now two matches pass, input should be disabled
        numberField.value = '1701';
        numberField.dispatchEvent(new Event('change', { bubbles: true }));

        await jest.runAllTimersAsync();

        expect(continueButton.disabled).toBe(true);

        // update the number field to a number that's not in the rule, again one match is passing, input should be enabled
        numberField.value = '99999';
        createField.checked = true;

        numberField.dispatchEvent(new Event('change', { bubbles: true }));

        await jest.runAllTimersAsync();

        expect(continueButton.disabled).toBe(false);

        // finally, set the checkbox field to unchecked, no matches should pass, input should be disabled
        createField.checked = false;

        numberField.dispatchEvent(new Event('change', { bubbles: true }));

        await jest.runAllTimersAsync();

        expect(continueButton.disabled).toBe(true);
      });

      it('should support the ability to match that `not` rules match', async () => {
        await setup(`
      <form data-controller="w-rules" data-action="change->w-rules#resolve" data-w-rules-match-value="not">
        <fieldset>
          <legend>Enter the registration number or opt to create a new number to continue.</legend>
          <input id="number" name="number" type="text" />
          <input id="create" name="create" type="checkbox" />
        </fieldset>
        <input
          id="continue"
          type="button"
          name="continue"
          data-w-rules-target="enable"
          data-w-rules-enable="${_({ create: ['on'], number: ['1701', '74656', '74913'] })}" />
      </form>`);

        const numberField = document.getElementById('number');
        const createField = document.getElementById('create');
        const continueButton = document.getElementById('continue');

        // enabled by default as there are not any matches
        expect(continueButton.disabled).toBe(false);

        // set the number field to a value that matches, there is now a match match, button should be disabled
        numberField.value = '1701';
        numberField.dispatchEvent(new Event('change', { bubbles: true }));

        await jest.runAllTimersAsync();

        expect(continueButton.disabled).toBe(true);

        // update the number field to a number that's not in the rule
        // update the checkbox so it does pass the rule
        // we will have one match is passing, input should be disabled
        numberField.value = '99999';
        createField.checked = true;

        numberField.dispatchEvent(new Event('change', { bubbles: true }));

        await jest.runAllTimersAsync();

        expect(continueButton.disabled).toBe(true);

        // finally, set the checkbox back to a non-passing state, no matches so the button should be enabled

        createField.checked = false;

        numberField.dispatchEvent(new Event('change', { bubbles: true }));

        await jest.runAllTimersAsync();

        expect(continueButton.disabled).toBe(false);
      });
    });
  });

  describe('conditionally showing a target', () => {
    it('should provide a way to conditionally show a target', async () => {
      const handleResolved = jest.fn();
      document.addEventListener('w-rules:resolved', handleResolved);

      await setup(`
    <form id="form" data-controller="w-rules" data-action="change->w-rules#resolve">
      <div
        id="alert"
        data-w-rules-target="show"
        data-w-rules="${_({ email: '' })}"
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

      // check the resolve event has been triggered
      expect(handleResolved).toHaveBeenCalledTimes(3);

      // remove the show target & check that the rules are not needing to be resolved
      alert.remove();

      emailField.dispatchEvent(new Event('change', { bubbles: true }));
      await jest.runAllTimersAsync();

      expect(handleResolved).toHaveBeenCalledTimes(3);
    });

    it('should support the ability to stop the effect from being applied by preventing the effect event', async () => {
      await setup(`
    <form id="form" data-controller="w-rules" data-action="change->w-rules#resolve">
      <div
        id="alert"
        data-w-rules-target="show"
        data-w-rules="${_({ email: '' })}"
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
      expect(eventListeners['w-rules:effect']).toHaveBeenCalledTimes(0);

      // prevent the effect event the first time it's dispatched

      eventListeners['w-rules:effect'].mockImplementationOnce((event) => {
        event.preventDefault();
      });

      // add a non-empty email value
      emailField.value = 'joe@email.co';

      emailField.dispatchEvent(new Event('change', { bubbles: true }));
      await jest.runAllTimersAsync();

      expect(eventListeners['w-rules:effect']).toHaveBeenCalledTimes(1);

      // check the element is still hidden
      expect(alert.hidden).toBe(false);

      // trigger the effect a second time
      emailField.dispatchEvent(
        new Event('change', { bubbles: true, cancelable: false }),
      );
      await jest.runAllTimersAsync();

      // assert that the event was dispatched and this time the effect has not been prevented
      expect(eventListeners['w-rules:effect']).toHaveBeenCalledTimes(2);

      expect(alert.hidden).toBe(true);
    });

    it('should ensure that the hidden attribute will be synced with the desired match once connected', async () => {
      await setup(`
    <form id="form" data-controller="w-rules">
      <fieldset>
        <input type="password" name="password" />
        <input type="email" name="email" />
        <input type="checkbox" name="remember" id="remember-me-field" />
      </fieldset>
      <label for="">This is my device.</label>
      <div
        id="alert"
        data-w-rules-target="show"
        data-w-rules="${_({ remember: 'on' })}"
      >
        Cookies will be saved to this device.
      </div>
      <button type="button">Continue</button>
    </form>`);

      // The checkbox is not checked, #alert is also not set with hidden (in supplied DOM)
      // Should update once connected
      expect(document.getElementById('alert').hidden).toBe(true);
    });

    describe('using different match values', () => {
      it('should support the ability to match one field rule', async () => {
        await setup(`
    <form id="form" data-controller="w-rules" data-action="change->w-rules#resolve" data-w-rules-match-value="one">
      <fieldset>
        <input type="checkbox" name="alpha" id="alpha" />
        <input type="checkbox" name="beta" id="beta" />
      </fieldset>
      <div
        id="alert"
        data-w-rules-target="show"
        data-w-rules="${_({ alpha: 'on', beta: 'on' })}"
      >
        Both items must be checked.
      </div>
      <button type="button">Continue</button>
    </form>`);

        expect(document.getElementById('alert').hidden).toBe(true);

        // check one input, so only one match passes, alert should be shown
        document.getElementById('alpha').checked = true;
        document
          .getElementById('alpha')
          .dispatchEvent(new Event('change', { bubbles: true }));
        await jest.runAllTimersAsync();

        expect(document.getElementById('alert').hidden).toBe(false);

        // check the other input, now two matches pass, alert should be hidden
        document.getElementById('beta').checked = true;
        document
          .getElementById('beta')
          .dispatchEvent(new Event('change', { bubbles: true }));
        await jest.runAllTimersAsync();

        expect(document.getElementById('alert').hidden).toBe(true);

        // uncheck the first input, so only one match passes, alert should be shown
        document.getElementById('alpha').checked = false;
        document
          .getElementById('alpha')
          .dispatchEvent(new Event('change', { bubbles: true }));
        await jest.runAllTimersAsync();

        expect(document.getElementById('alert').hidden).toBe(false);
      });

      it('should support the ability to provide the match via params that override other declarations when an event is used', async () => {
        await setup(`
    <form id="form" data-controller="w-rules" data-action="change->w-rules#resolve" data-w-rules-match-value="all" data-w-rules-match-param="one">
      <fieldset>
        <input type="checkbox" name="alpha" id="alpha" />
        <input type="checkbox" name="beta" id="beta" />
      </fieldset>
      <div
        id="alert"
        data-w-rules-target="show"
        data-w-rules="${_({ alpha: 'on', beta: 'on' })}"
        data-w-rules-match="all"
        data-w-rules-show-match="not"
      >
        Both items must be checked.
      </div>
      <button type="button">Continue</button>
    </form>`);

        // initial load should use the match value 'not'
        expect(document.getElementById('alert').hidden).toBe(false);

        // check one input, so only one match passes, alert should be shown due to now using event with params
        document.getElementById('alpha').checked = true;
        document
          .getElementById('alpha')
          .dispatchEvent(new Event('change', { bubbles: true }));
        await jest.runAllTimersAsync();

        expect(document.getElementById('alert').hidden).toBe(false);

        // check the other input, now two matches pass, alert should be hidden
        document.getElementById('beta').checked = true;
        document
          .getElementById('beta')
          .dispatchEvent(new Event('change', { bubbles: true }));
        await jest.runAllTimersAsync();

        expect(document.getElementById('alert').hidden).toBe(true);

        // uncheck the first input, so only one match passes, alert should be shown
        document.getElementById('alpha').checked = false;
        document
          .getElementById('alpha')
          .dispatchEvent(new Event('change', { bubbles: true }));
        await jest.runAllTimersAsync();

        expect(document.getElementById('alert').hidden).toBe(false);
      });

      it('should support the ability to match that `not` rules match', async () => {
        await setup(`
    <form id="form" data-controller="w-rules" data-action="change->w-rules#resolve" data-w-rules-match-value="not">
      <fieldset>
        <input type="password" name="password" id="password" />
        <input type="email" name="email" id="email" />
        <input type="checkbox" name="remember" id="remember" />
      </fieldset>
      <div
        id="alert"
        data-w-rules-target="show"
        data-w-rules="${_({ remember: 'not', password: '', email: '' })}"
      >
        Thank you for entering all inputs.
      </div>
      <button type="button">Continue</button>
    </form>`);

        expect(document.getElementById('alert').hidden).toBe(true);

        // update one field - it should still be hidden
        document.getElementById('password').value = 'password';
        document
          .getElementById('password')
          .dispatchEvent(new Event('change', { bubbles: true }));
        await jest.runAllTimersAsync();

        expect(document.getElementById('alert').hidden).toBe(true);

        // update the other - both have a value, so the target should be shown
        document.getElementById('email').value = 'email@example.com';
        document
          .getElementById('email')
          .dispatchEvent(new Event('change', { bubbles: true }));

        await jest.runAllTimersAsync();

        expect(document.getElementById('alert').hidden).toBe(false);
      });

      it('should support the ability to provide the match value via the target element generically', async () => {
        await setup(`
    <form id="form" data-controller="w-rules" data-action="change->w-rules#resolve">
      <fieldset>
        <input type="password" name="password" id="password" />
        <input type="email" name="email" id="email" />
        <input type="checkbox" name="remember" id="remember" />
      </fieldset>
      <div
        id="alert"
        data-w-rules-target="show"
        data-w-rules="${_({ remember: 'not', password: '', email: '' })}"
        data-w-rules-match="not"
      >
        Thank you for entering all inputs.
      </div>
      <button type="button">Continue</button>
    </form>`);

        expect(document.getElementById('alert').hidden).toBe(true);

        // update one field - it should still be hidden
        document.getElementById('password').value = 'password';
        document
          .getElementById('password')
          .dispatchEvent(new Event('change', { bubbles: true }));
        await jest.runAllTimersAsync();

        expect(document.getElementById('alert').hidden).toBe(true);

        // update the other - both have a value, so the target should be shown
        document.getElementById('email').value = 'email@example.com';
        document
          .getElementById('email')
          .dispatchEvent(new Event('change', { bubbles: true }));

        await jest.runAllTimersAsync();

        expect(document.getElementById('alert').hidden).toBe(false);
      });

      it('should support the ability to provide the match value via the target element for the specific action case', async () => {
        await setup(`
    <form id="form" data-controller="w-rules" data-action="change->w-rules#resolve">
      <fieldset>
        <input type="password" name="password" id="password" />
        <input type="email" name="email" id="email" />
        <input type="checkbox" name="remember" id="remember" />
      </fieldset>
      <div
        id="alert"
        data-w-rules-target="show"
        data-w-rules="${_({ remember: 'not', password: '', email: '' })}"
        data-w-rules-show-match="not"
        data-w-rules-match="one"
      >
        Thank you for entering all inputs.
      </div>
      <button type="button">Continue</button>
    </form>`);

        expect(document.getElementById('alert').hidden).toBe(true);

        // update one field - it should still be hidden
        document.getElementById('password').value = 'password';
        document
          .getElementById('password')
          .dispatchEvent(new Event('change', { bubbles: true }));
        await jest.runAllTimersAsync();

        expect(document.getElementById('alert').hidden).toBe(true);

        // update the other - both have a value, so the target should be shown
        document.getElementById('email').value = 'email@example.com';
        document
          .getElementById('email')
          .dispatchEvent(new Event('change', { bubbles: true }));

        await jest.runAllTimersAsync();

        expect(document.getElementById('alert').hidden).toBe(false);
      });
    });

    describe('using as a filtered-select', () => {
      beforeEach(async () => {
        await setup(`
  <form
    data-controller="w-rules"
    data-action="change->w-rules#resolve"
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
        data-w-rules-target="show"
        data-w-rules='${_({ continent: ['', 3] })}'
      >
        China
      </option>
      <option
        value="2"
        data-w-rules-target="show"
        data-w-rules='${_({ continent: ['', 2] })}'
      >
        Egypt
      </option>
      <option
        value="3"
        data-w-rules-target="show"
        data-w-rules='${_({ continent: ['', 1] })}'
      >
        France
      </option>
      <option
        value="4"
        data-w-rules-target="show"
        data-w-rules='${_({ continent: ['', 1] })}'
      >
        Germany
      </option>
      <option
        value="5"
        data-w-rules-target="show"
        data-w-rules='${_({ continent: ['', 3] })}'
      >
        Japan
      </option>
      <option
        value="6"
        data-w-rules-target="show"
        data-w-rules='${_({ continent: ['', 1, 3] })}'
      >
        Russia
      </option>
      <option
        value="7"
        data-w-rules-target="show"
        data-w-rules='${_({ continent: ['', 2] })}'
      >
        South
       Africa</option>
      <option
        value="8"
        data-w-rules-target="show"
        data-w-rules='${_({ continent: ['', 1, 3] })}'
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
    });
  });
});
