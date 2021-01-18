import './telepath';
import './widgets';

import $ from 'jquery';
window.$ = $;

describe('telepath: wagtail.widgets.Widget', () => {
  let boundWidget;

  beforeEach(() => {
    // Create a placeholder to render the widget
    document.body.innerHTML = '<div id="placeholder"></div>';

    // Unpack and render a simple text block widget
    const widgetDef = window.telepath.unpack({
      _type: 'wagtail.widgets.Widget',
      _args: [
        '<input type="text" name="__NAME__" maxlength="255" id="__ID__">',
        '__ID__'
      ]
    });
    boundWidget = widgetDef.render($('#placeholder'), 'the-name', 'the-id', 'The Value');
  });

  test('it renders correctly', () => {
    expect(document.body.innerHTML).toBe('<input type="text" name="the-name" maxlength="255" id="the-id">');
    expect(document.querySelector('input').value).toBe('The Value');
  });

  test('getValue() returns the current value', () => {
    expect(boundWidget.getValue()).toBe('The Value');
  });

  test('getState() returns the current state', () => {
    expect(boundWidget.getState()).toBe('The Value');
  });

  test('setState() changes the current state', () => {
    boundWidget.setState('The new Value');
    expect(document.querySelector('input').value).toBe('The new Value');
  });

  test('focus() focuses the text input', () => {
    boundWidget.focus();
    expect(document.activeElement).toBe(document.querySelector('input'));
  });
});

describe('telepath: wagtail.widgets.RadioSelect', () => {
  let boundWidget;

  beforeEach(() => {
    // Create a placeholder to render the widget
    document.body.innerHTML = '<div id="placeholder"></div>';

    // Unpack and render a radio select widget
    const widgetDef = window.telepath.unpack({
      _type: 'wagtail.widgets.RadioSelect',
      _args: [
        `<ul id="__ID__">
          <li>
            <label for="__ID___0">
            <input type="radio" name="__NAME__" value="tea" id="__ID___0"> Tea</label>
          </li>
          <li>
            <label for="__ID___1">
            <input type="radio" name="__NAME__" value="coffee" id="__ID___1"> Coffee</label>
          </li>
        </ul>`,
        '__ID___0'
      ]
    });
    boundWidget = widgetDef.render($('#placeholder'), 'the-name', 'the-id', 'tea');
  });

  test('it renders correctly', () => {
    expect(document.body.innerHTML).toMatchSnapshot();
    expect(document.querySelector('input[value="tea"]').checked).toBe(true);
    expect(document.querySelector('input[value="coffee"]').checked).toBe(false);
  });

  test('getValue() returns the current value', () => {
    expect(boundWidget.getValue()).toBe('tea');
  });

  test('getState() returns the current state', () => {
    expect(boundWidget.getState()).toBe('tea');
  });

  test('setState() changes the current state', () => {
    boundWidget.setState('coffee');
    expect(document.querySelector('input[value="tea"]').checked).toBe(false);
    expect(document.querySelector('input[value="coffee"]').checked).toBe(true);
  });

  test('focus() focuses the text input', () => {
    boundWidget.focus();

    // Note: This widget always focuses the last element
    expect(document.activeElement).toBe(document.querySelector('input[value="coffee"]'));
  });
});
