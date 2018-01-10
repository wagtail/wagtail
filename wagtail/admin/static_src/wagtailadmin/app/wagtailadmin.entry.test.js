const wagtail = require('wagtail-client');
wagtail.initExplorer = jest.fn();

document.addEventListener = jest.fn();

require('./wagtailadmin.entry');

describe('wagtailadmin.entry', () => {
  const [event, listener] = document.addEventListener.mock.calls[0];

  it('DOMContentLoaded', () => {
    expect(event).toBe('DOMContentLoaded');
  });

  it('init', () => {
    listener();
    expect(wagtail.initExplorer).not.toHaveBeenCalled();
  });

  it('init with DOM', () => {
    document.body.innerHTML = '<div data-explorer-menu></div><div data-explorer-start-page></div>';
    listener();
    expect(wagtail.initExplorer).toHaveBeenCalled();
  });
});
