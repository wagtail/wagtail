import * as tippy from 'tippy.js';
import { initTooltips } from './initTooltips';

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
