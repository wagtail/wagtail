import { initAnchoredPanels, initCollapsiblePanels } from './panels';

describe('initAnchoredPanels', () => {
  beforeEach(() => {
    Element.prototype.scrollIntoView = jest.fn();
  });

  afterEach(() => {
    document.body.innerHTML = '';
    window.location.hash = '';
  });

  it('expands collapsed ancestor panels before scrolling to the contentpath target', () => {
    document.body.innerHTML = /* html */ `
      <section class="w-panel collapsed" data-panel id="appearance-section">
        <div class="w-panel__header">
          <button class="w-panel__toggle" type="button" data-panel-toggle aria-controls="appearance-content" aria-expanded="true"></button>
          <h2 class="w-panel__heading" data-panel-heading>Appearance</h2>
        </div>
        <div id="appearance-content" class="w-panel__content">
          <div data-contentpath="logo"><input id="logo" type="text"></div>
        </div>
      </section>
    `;
    window.location.hash = '#:w:contentpath=logo';

    initCollapsiblePanels();
    expect(
      document
        .querySelector('[data-panel-toggle]')
        .getAttribute('aria-expanded'),
    ).toEqual('false');

    initAnchoredPanels();

    expect(
      document
        .querySelector('[data-panel-toggle]')
        .getAttribute('aria-expanded'),
    ).toEqual('true');
    expect(
      document.getElementById('appearance-content').hasAttribute('hidden'),
    ).toBe(false);
  });

  it('leaves panels that are not collapsed alone', () => {
    document.body.innerHTML = /* html */ `
      <section class="w-panel" data-panel id="appearance-section">
        <div class="w-panel__header">
          <button class="w-panel__toggle" type="button" data-panel-toggle aria-controls="appearance-content" aria-expanded="true"></button>
        </div>
        <div id="appearance-content" class="w-panel__content">
          <div data-contentpath="logo"><input id="logo" type="text"></div>
        </div>
      </section>
    `;
    window.location.hash = '#:w:contentpath=logo';

    initCollapsiblePanels();
    initAnchoredPanels();

    expect(
      document
        .querySelector('[data-panel-toggle]')
        .getAttribute('aria-expanded'),
    ).toEqual('true');
    expect(
      document.getElementById('appearance-content').hasAttribute('hidden'),
    ).toBe(false);
  });

  it('expands multiple nested collapsed panels', () => {
    document.body.innerHTML = /* html */ `
      <section class="w-panel collapsed" data-panel id="outer-section">
        <div class="w-panel__header">
          <button class="w-panel__toggle" type="button" data-panel-toggle aria-controls="outer-content" aria-expanded="true"></button>
        </div>
        <div id="outer-content" class="w-panel__content">
          <section class="w-panel collapsed" data-panel id="inner-section">
            <div class="w-panel__header">
              <button class="w-panel__toggle" type="button" data-panel-toggle aria-controls="inner-content" aria-expanded="true"></button>
            </div>
            <div id="inner-content" class="w-panel__content">
              <div data-contentpath="logo"><input id="logo" type="text"></div>
            </div>
          </section>
        </div>
      </section>
    `;
    window.location.hash = '#:w:contentpath=logo';

    initCollapsiblePanels();
    initAnchoredPanels();

    const toggles = document.querySelectorAll('[data-panel-toggle]');
    expect(toggles.length).toEqual(2);
    toggles.forEach((toggle) => {
      expect(toggle.getAttribute('aria-expanded')).toEqual('true');
    });
    expect(
      document.getElementById('outer-content').hasAttribute('hidden'),
    ).toBe(false);
    expect(
      document.getElementById('inner-content').hasAttribute('hidden'),
    ).toBe(false);
  });

  it('does not error when there is no contentpath target', () => {
    document.body.innerHTML = '';
    window.location.hash = '#:w:contentpath=missing';

    expect(() => initAnchoredPanels()).not.toThrow();
  });
});
