jest.mock('../..');

document.addEventListener = jest.fn();

require('./core');

describe('core', () => {
  const [event] = document.addEventListener.mock.calls[0];

  it('exposes the Stimulus application instance for reuse', () => {
    expect(Object.keys(window.wagtail.app)).toEqual(
      expect.arrayContaining(['debug', 'logger']),
    );

    expect(window.wagtail.app.load).toBeInstanceOf(Function);
    expect(window.wagtail.app.register).toBeInstanceOf(Function);
  });

  it('exposes components for reuse', () => {
    expect(Object.keys(window.wagtail.components)).toEqual(['Icon', 'Portal']);
  });

  it('exposes the Stimulus module for reuse', () => {
    expect(Object.keys(window.StimulusModule)).toEqual(
      expect.arrayContaining(['Application', 'Controller']),
    );
  });

  it('DOMContentLoaded', () => {
    expect(event).toBe('DOMContentLoaded');
  });
});
