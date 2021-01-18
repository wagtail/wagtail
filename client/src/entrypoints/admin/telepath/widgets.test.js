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
