import { AdminDateInput, AdminDateTimeInput, AdminTimeInput } from './index';

describe('AdminDateInput', () => {
  let boundWidget;

  beforeEach(() => {
    window.initDateChooser = jest.fn();

    // Create a placeholder to render the widget
    document.body.innerHTML = '<div id="placeholder"></div>';

    // Render
    const widgetDef = new AdminDateInput({
      dayOfWeekStart: 0,
      format: 'Y-m-d',
    });
    boundWidget = widgetDef.render(
      document.getElementById('placeholder'),
      'the-name',
      'the-id',
      '2021-01-19',
    );
  });

  test('it renders correctly', () => {
    expect(document.body.innerHTML).toBe(
      '<input type="text" name="the-name" id="the-id">',
    );
    expect(document.querySelector('input').value).toBe('2021-01-19');
  });

  test('window.initDateChooser was called', () => {
    expect(window.initDateChooser.mock.calls.length).toBe(1);
    expect(window.initDateChooser.mock.calls[0][0]).toBe('the-id');
    expect(window.initDateChooser.mock.calls[0][1]).toEqual({
      dayOfWeekStart: 0,
      format: 'Y-m-d',
    });
  });

  test('getValue() returns the current value', () => {
    expect(boundWidget.getValue()).toBe('2021-01-19');
  });

  test('getState() returns the current state', () => {
    expect(boundWidget.getState()).toBe('2021-01-19');
  });

  test('setState() changes the current state', () => {
    boundWidget.setState('2021-01-20');
    expect(document.querySelector('input').value).toBe('2021-01-20');
  });

  test('setInvalid() sets aria-invalid attribute', () => {
    boundWidget.setInvalid(true);
    expect(document.querySelector('input').getAttribute('aria-invalid')).toBe(
      'true',
    );
    boundWidget.setInvalid(false);
    expect(
      document.querySelector('input').getAttribute('aria-invalid'),
    ).toBeNull();
  });

  test('focus() focuses the input', () => {
    boundWidget.focus();
    expect(document.activeElement).toBe(document.querySelector('input'));
  });
});

describe('AdminTimeInput', () => {
  let boundWidget;

  beforeEach(() => {
    window.initTimeChooser = jest.fn();

    // Create a placeholder to render the widget
    document.body.innerHTML = '<div id="placeholder"></div>';

    // Render
    const widgetDef = new AdminTimeInput({
      format: 'H:i',
      formatTime: 'H:i',
    });
    boundWidget = widgetDef.render(
      document.getElementById('placeholder'),
      'the-name',
      'the-id',
      '11:59',
    );
  });

  test('it renders correctly', () => {
    expect(document.body.innerHTML).toBe(
      '<input type="text" name="the-name" id="the-id">',
    );
    expect(document.querySelector('input').value).toBe('11:59');
  });

  test('window.initTimeChooser was called', () => {
    expect(window.initTimeChooser.mock.calls.length).toBe(1);
    expect(window.initTimeChooser.mock.calls[0][0]).toBe('the-id');
    expect(window.initTimeChooser.mock.calls[0][1]).toEqual({
      format: 'H:i',
      formatTime: 'H:i',
    });
  });

  test('getValue() returns the current value', () => {
    expect(boundWidget.getValue()).toBe('11:59');
  });

  test('getState() returns the current state', () => {
    expect(boundWidget.getState()).toBe('11:59');
  });

  test('setState() changes the current state', () => {
    boundWidget.setState('12:34');
    expect(document.querySelector('input').value).toBe('12:34');
  });

  test('setInvalid() sets aria-invalid attribute', () => {
    boundWidget.setInvalid(true);
    expect(document.querySelector('input').getAttribute('aria-invalid')).toBe(
      'true',
    );
    boundWidget.setInvalid(false);
    expect(
      document.querySelector('input').getAttribute('aria-invalid'),
    ).toBeNull();
  });

  test('focus() focuses the input', () => {
    boundWidget.focus();
    expect(document.activeElement).toBe(document.querySelector('input'));
  });
});

describe('AdminDateTimeInput', () => {
  let boundWidget;

  beforeEach(() => {
    window.initDateTimeChooser = jest.fn();

    // Create a placeholder to render the widget
    document.body.innerHTML = '<div id="placeholder"></div>';

    // Render
    const widgetDef = new AdminDateTimeInput({
      dayOfWeekStart: 0,
      format: 'Y-m-d H:i',
      formatTime: 'H:i',
    });
    boundWidget = widgetDef.render(
      document.getElementById('placeholder'),
      'the-name',
      'the-id',
      '2021-01-19 11:59',
    );
  });

  test('it renders correctly', () => {
    expect(document.body.innerHTML).toBe(
      '<input type="text" name="the-name" id="the-id">',
    );
    expect(document.querySelector('input').value).toBe('2021-01-19 11:59');
  });

  test('window.initDateTimeChooser was called', () => {
    expect(window.initDateTimeChooser.mock.calls.length).toBe(1);
    expect(window.initDateTimeChooser.mock.calls[0][0]).toBe('the-id');
    expect(window.initDateTimeChooser.mock.calls[0][1]).toEqual({
      dayOfWeekStart: 0,
      format: 'Y-m-d H:i',
      formatTime: 'H:i',
    });
  });

  test('getValue() returns the current value', () => {
    expect(boundWidget.getValue()).toBe('2021-01-19 11:59');
  });

  test('getState() returns the current state', () => {
    expect(boundWidget.getState()).toBe('2021-01-19 11:59');
  });

  test('setState() changes the current state', () => {
    boundWidget.setState('2021-01-20 12:34');
    expect(document.querySelector('input').value).toBe('2021-01-20 12:34');
  });

  test('setInvalid() sets aria-invalid attribute', () => {
    boundWidget.setInvalid(true);
    expect(document.querySelector('input').getAttribute('aria-invalid')).toBe(
      'true',
    );
    boundWidget.setInvalid(false);
    expect(
      document.querySelector('input').getAttribute('aria-invalid'),
    ).toBeNull();
  });

  test('focus() focuses the input', () => {
    boundWidget.focus();
    expect(document.activeElement).toBe(document.querySelector('input'));
  });

  test('getTextLabel() returns the text of entered value', () => {
    expect(boundWidget.getTextLabel()).toBe('2021-01-19 11:59');
  });
});
