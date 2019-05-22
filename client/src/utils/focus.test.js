import { initFocusOutline } from './focus';

describe('initFocusOutline', () => {
  beforeEach(() => {
    document.body.classList.add('focus-outline-on');
  });

  it('removes styles on init', () => {
    initFocusOutline();
    expect(document.body.className).toBe('focus-outline-off');
  });

  it('adds styles when tabbing', () => {
    initFocusOutline();
    window.dispatchEvent(
      Object.assign(new Event('keydown'), {
        keyCode: 9
      })
    );
    expect(document.body.className).toBe('focus-outline-on');
  });

  it('does not change styles when using keys that are not tab', () => {
    initFocusOutline();
    window.dispatchEvent(new Event('keydown'));
    expect(document.body.className).toBe('focus-outline-off');
  });

  it('removes styles when using a mouse', () => {
    window.dispatchEvent(
      Object.assign(new Event('keydown'), {
        keyCode: 9
      })
    );
    window.dispatchEvent(new Event('mousedown'));
    expect(document.body.className).toBe('focus-outline-off');
  });

  it('removes styles when using a touch screen', () => {
    window.dispatchEvent(
      Object.assign(new Event('keydown'), {
        keyCode: 9
      })
    );
    window.dispatchEvent(new Event('touchstart'));
    expect(document.body.className).toBe('focus-outline-off');
  });
});
