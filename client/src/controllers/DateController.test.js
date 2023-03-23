import $ from 'jquery';

import { Application } from '@hotwired/stimulus';
import { DateController } from './DateController';

jest.useFakeTimers();

describe('DateController', () => {
  window.wagtailConfig = {
    STRINGS: { MONTHS: ['JAN'], WEEKDAYS: ['MON'], WEEKDAYS_SHORT: ['M'] },
  };

  const datetimepickerMock = jest.fn();
  let application;

  beforeEach(() => {
    jest.clearAllMocks();

    $.fn.datetimepicker = datetimepickerMock;
    $.datetimepicker = datetimepickerMock;
    datetimepickerMock.defaults = { i18n: {} };
    datetimepickerMock.setLocale = jest.fn();

    application?.unload('w-date');
    application?.stop();
  });

  it('should set the default translations based on global config when controller is registered', () => {
    expect(datetimepickerMock.defaults.i18n).toEqual({});
    expect(datetimepickerMock.setLocale).not.toHaveBeenCalled();

    application = Application.start();
    application.register('w-date', DateController);

    expect(datetimepickerMock.defaults.i18n).toHaveProperty(
      'wagtail_custom_locale',
      { months: ['JAN'], dayOfWeek: ['MON'], dayOfWeekShort: ['M'] },
    );
    expect(datetimepickerMock.setLocale).toHaveBeenCalledWith(
      'wagtail_custom_locale',
    );
  });

  it('should create a date picker only by default', async () => {
    document.body.innerHTML = `
    <main>
      <input id="date" type="text" data-controller="w-date" value="2020-01-01" />
      <ul id="datepicker-overlay" class="_MOCK_ xdsoft_datepicker">
        <li class="A xdsoft_current xdsoft_today"></li>
        <li class="B xdsoft_current"></li>
      </ul>
    </main>
    `;

    application = Application.start();
    application.register('w-date', DateController);

    // await the next render
    await Promise.resolve();

    // ensure the jQuery plugin gets correctly called
    expect(datetimepickerMock).toHaveBeenLastCalledWith({
      closeOnDateSelect: true,
      format: 'Y-m-d',
      onChangeDateTime: expect.any(Function),
      onGenerate: expect.any(Function),
      scrollInput: false,
      timepicker: false,
    });

    // check the hide current functionality works as expected
    datetimepickerMock.mock.calls[0][0].onGenerate.apply(
      [document.getElementById('datepicker-overlay')],
      [new Date(), document.getElementById('date')],
    );

    expect(
      document.querySelectorAll('.A.xdsoft_current.xdsoft_today').length,
    ).toBe(1);
    expect(document.querySelectorAll('.B.xdsoft_current').length).toBe(0);

    const onChange = jest.fn();

    // check that changes to the datetimepicker will fire a change event that bubbles
    document.addEventListener('change', onChange);
    datetimepickerMock.mock.calls[0][0].onChangeDateTime();

    expect(onChange).toHaveBeenCalledTimes(1);

    // ensure that the jQuery plugin gets removed on disconnect
    document.getElementById('date').remove();

    await Promise.resolve();

    expect(datetimepickerMock).toHaveBeenLastCalledWith('destroy');
  });

  it('should set up the ability to trigger a non-obtrusive focus shortly after creation', async () => {
    document.body.innerHTML = `
    <section id="section">
      <input id="date" type="text" data-controller="w-date" />
      <button type="button">A target</button>
    </section>
    `;

    application = Application.start();
    application.register('w-date', DateController);

    // await the next render
    await Promise.resolve();

    const dateField = document.getElementById('date');

    dateField.dispatchEvent(
      new CustomEvent('wagtail:telepath-widget-focus', {
        detail: { soft: true },
      }),
    );

    jest.runAllTimers();

    const section = document.getElementById('section');

    expect(document.activeElement).toBe(section);
    expect(section.getAttribute('tabindex')).toBe('-1');
    expect(datetimepickerMock).toHaveBeenLastCalledWith('hide');

    // remove tabindex once something else gains focus
    document.querySelector('button').focus();
    expect(section.getAttribute('tabindex')).toBeNull();

    // on focus triggered after threshold, should act as normal
    dateField.focus();
    expect(document.activeElement).toBe(dateField);
  });

  it('should support a datetime picker mode', async () => {
    document.body.innerHTML = `
    <section id="section">
      <input id="date" type="text" data-controller="w-date" data-w-date-mode-value="datetime" />
    </section>
    `;

    application = Application.start();
    application.register('w-date', DateController);

    await Promise.resolve();

    expect(datetimepickerMock).toHaveBeenLastCalledWith({
      closeOnDateSelect: true,
      format: 'Y-m-d H:i',
      onChangeDateTime: expect.any(Function),
      onGenerate: expect.any(Function),
      scrollInput: false,
    });
  });

  it('should support a time picker mode', async () => {
    document.body.innerHTML = `
    <section id="section">
      <input id="date" type="text" data-controller="w-date" data-w-date-mode-value="time" />
    </section>
    `;

    application = Application.start();
    application.register('w-date', DateController);

    await Promise.resolve();

    expect(datetimepickerMock).toHaveBeenLastCalledWith({
      closeOnDateSelect: true,
      datepicker: false,
      format: 'H:i',
      onChangeDateTime: expect.any(Function),
      onGenerate: expect.any(Function),
      scrollInput: false,
    });
  });

  it('should support additional options passed in', async () => {
    document.body.innerHTML = `
    <section id="section">
      <input id="date" type="text" data-controller="w-date" data-w-date-mode-value="date" />
    </section>
    `;

    document.getElementById('date').dataset.wDateOptionsValue = JSON.stringify({
      closeOnDateSelect: false,
      format: 'AA BB YY',
      onGenerate: null, // should be ignored
      scrollInput: true,
      xOther: true,
    });

    application = Application.start();
    application.register('w-date', DateController);

    await Promise.resolve();

    expect(datetimepickerMock).toHaveBeenLastCalledWith({
      closeOnDateSelect: false,
      format: 'AA BB YY',
      onChangeDateTime: expect.any(Function),
      onGenerate: expect.any(Function), // not null
      scrollInput: true,
      timepicker: false,
      xOther: true,
    });
  });
});
