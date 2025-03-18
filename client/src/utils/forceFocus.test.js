import { forceFocus } from './forceFocus';

jest.useFakeTimers();

describe('forceFocus', () => {
  it('should focus on the provided element', async () => {
    document.body.innerHTML = '<input id="input" type="text" />';

    const element = document.getElementById('input');
    forceFocus(element);

    expect(document.activeElement).toBe(document.body);

    await jest.runAllTimersAsync();

    expect(element.scrollIntoView).toHaveBeenCalled();
    expect(document.activeElement).toBe(element);
  });

  it('should focus on an element that is just added', async () => {
    document.body.innerHTML = '';

    const element = document.createElement('input');
    element.id = 'input';
    document.body.appendChild(element);

    forceFocus(element);

    expect(document.activeElement).toBe(document.body);

    await jest.runAllTimersAsync();

    expect(element.scrollIntoView).toHaveBeenCalled();
    expect(document.activeElement).toBe(element);
  });

  it('should add tabIndex to the element if it does not have it', async () => {
    document.body.innerHTML =
      '<div id="element">CONTENT</div><button id="button" type="button">BUTTON</button>';

    const element = document.getElementById('element');

    expect(element.getAttribute('tabindex')).toBe(null);

    forceFocus(element);

    await jest.runAllTimersAsync();

    expect(element.getAttribute('tabindex')).toBe('-1');

    expect(element.scrollIntoView).toHaveBeenCalled();
    expect(document.activeElement).toBe(element);

    // focus on a different element, check that the tabIndex is removed
    const button = document.getElementById('button');
    button.focus();
    expect(document.activeElement).toBe(button);

    expect(element.getAttribute('tabindex')).toBe(null);
  });
});
