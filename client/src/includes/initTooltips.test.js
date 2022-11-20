import * as tippy from 'tippy.js';
import { initTooltips, initModernDropdown } from './initTooltips';

jest.spyOn(tippy, 'default');

beforeEach(() => jest.clearAllMocks());

describe('initTooltips', () => {
  it('should call the Tippy util with the [data-tippy-content] attribute', () => {
    expect(tippy.default).not.toHaveBeenCalled();
    initTooltips();
    expect(tippy.default).toHaveBeenCalledWith('[data-tippy-content]', {
      plugins: [expect.objectContaining({ name: 'hideOnEsc' })],
    });
  });
});

describe('initModernDropdown', () => {
  it('should not call Tippy if there is no element with [data-button-with-dropdown]', () => {
    expect(tippy.default).not.toHaveBeenCalled();

    initModernDropdown();

    expect(tippy.default).not.toHaveBeenCalled();
  });

  it('should call the Tippy util with the [data-button-with-dropdown-toggle] attribute', () => {
    const html = `
    <div data-button-with-dropdown>
      <button id="button" data-button-with-dropdown-toggle>...</button>
      <div id="content" data-button-with-dropdown-content>
        Content
      </div>
    </div>`;
    document.body.innerHTML = html;

    const content = document.getElementById('content');

    expect(tippy.default).not.toHaveBeenCalled();

    initModernDropdown();

    expect(tippy.default).toHaveBeenLastCalledWith(
      document.getElementById('button'),
      expect.objectContaining({
        content,
        trigger: 'click',
        interactive: true,
        theme: 'dropdown',
        placement: 'bottom',
      }),
    );
  });
});
