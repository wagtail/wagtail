jest.mock('../..');

document.addEventListener = jest.fn();

require('./wagtailadmin');

describe('wagtailadmin', () => {
  const [event] = document.addEventListener.mock.calls[0];

  it('exposes components for reuse', () => {
    expect(Object.keys(window.wagtail.components)).toEqual(['Icon', 'Portal']);
  });

  it('DOMContentLoaded', () => {
    expect(event).toBe('DOMContentLoaded');
  });
});
