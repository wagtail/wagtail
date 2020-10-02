const wagtailConfig = require('../config/wagtailConfig');
const { initIE11Warning } = require('./initIE11Warning');

describe('initIE11Warning', () => {
  it('skips logic if the page has no warnings', () => {
    initIE11Warning();
  });

  it('shows warnings in IE11', () => {
    wagtailConfig.IS_IE11 = true;
    document.body.innerHTML = '<p data-ie11-warning hidden>Test</p>';
    initIE11Warning();
    expect(document.querySelector('[data-ie11-warning]').hidden).toBe(false);
  });

  it('no warnings for other browsers', () => {
    wagtailConfig.IS_IE11 = false;
    document.body.innerHTML = '<p data-ie11-warning hidden>Test</p>';
    initIE11Warning();
    expect(document.querySelector('[data-ie11-warning]').hidden).toBe(true);
  });
});
