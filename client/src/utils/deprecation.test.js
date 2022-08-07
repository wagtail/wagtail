import * as allDeprecationWarnings from './deprecation';

// jest.spyOn(console, 'info').mockImplementation(() => {});
// const warn = jest.spyOn(console, 'warn').mockImplementation(() => {});

describe('deprecation warnings', () => {
  const warn = jest.fn();
  document.addEventListener(
    'wagtail:development-warning',
    ({ detail, target }) => warn({ detail, target }),
  );

  beforeEach(jest.resetAllMocks);

  // so we do not have to update the tests each new version - just grab one warning export
  const [removedInWagtailVersionWarning] = Object.values(
    allDeprecationWarnings,
  );

  it('should export a warning function', () => {
    expect(removedInWagtailVersionWarning).toBeInstanceOf(Function);
  });

  it('should dispatch a warning via custom event dispatch', () => {
    expect(warn).not.toHaveBeenCalled();
    removedInWagtailVersionWarning('some message', {
      data: { additional: true },
    });

    expect(warn).toHaveBeenCalledWith({
      detail: expect.objectContaining({
        message: 'some message',
        title: expect.stringContaining('Warning'),
        data: { additional: true },
      }),
      target: window.document,
    });
  });

  it('should allow an explicit target to be supplied', () => {
    document.body.innerHTML = '<h1 id="header">Header</h1>';
    const header = document.getElementById('header');

    expect(warn).not.toHaveBeenCalled();

    removedInWagtailVersionWarning('this element is gonna break!', {
      target: header,
    });

    expect(warn).toHaveBeenCalledWith({
      detail: expect.objectContaining({
        message: 'this element is gonna break!',
        title: expect.stringContaining('Warning'),
        data: null,
      }),
      target: header,
    });
  });
});
