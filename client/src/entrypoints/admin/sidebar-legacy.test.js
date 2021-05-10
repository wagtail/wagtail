jest.mock('../../components/Explorer');

const Explorer = require('../../components/Explorer');

document.addEventListener = jest.fn();

require('./sidebar-legacy');

describe('sidebar-legacy', () => {
  const [event, listener] = document.addEventListener.mock.calls[0];

  it('DOMContentLoaded', () => {
    expect(event).toBe('DOMContentLoaded');
  });

  it('init', () => {
    listener();
    expect(Explorer.initExplorer).not.toHaveBeenCalled();
  });

  it('init with DOM', () => {
    document.body.innerHTML = '<div data-explorer-menu></div><div data-explorer-start-page></div>';
    listener();
    expect(Explorer.initExplorer).toHaveBeenCalled();
  });
});
