import { Application } from '@hotwired/stimulus';
import { DropdownController } from './DropdownController';

describe('DropdownController', () => {
  let application;

  beforeEach(async () => {
    document.body.innerHTML = `
<div data-controller="w-dropdown" data-action="custom:show->w-dropdown#show custom:hide->w-dropdown#hide">
  <button type="button" data-w-dropdown-target="toggle" aria-label="Actions"></button>
  <div data-w-dropdown-target="content">
    <a href="/">Option</a>
  </div>
</div>`;

    application = Application.start();
    application.register('w-dropdown', DropdownController);

    await Promise.resolve();

    // set all animation durations to 0 so that tests can ignore animation delays
    // Tippy relies on transitionend which is not yet supported in JSDom
    // https://github.com/jsdom/jsdom/issues/1781

    document
      .querySelectorAll('[data-controller="w-dropdown"]')
      .forEach((element) => {
        application
          .getControllerForElementAndIdentifier(element, 'w-dropdown')
          .tippy.setProps({ duration: 0 }); // tippy will merge props with whatever has already been set
      });
  });

  afterEach(() => {
    jest.restoreAllMocks();
    application?.stop();
  });

  it('initialises Tippy.js on connect and shows content in a dropdown', () => {
    const toggle = document.querySelector('[data-w-dropdown-target="toggle"]');
    const content = document.querySelector(
      '[data-w-dropdown-target="content"]',
    );
    expect(toggle.getAttribute('aria-expanded')).toBe('false');
    expect(content).toBe(null);

    toggle.dispatchEvent(new Event('click'));

    const expandedContent = document.querySelectorAll('[role="tooltip"]');
    expect(expandedContent).toHaveLength(1);

    expect(expandedContent[0].innerHTML).toContain('<a href="/">Option</a>');
  });

  it('triggers custom event on activation', async () => {
    const toggle = document.querySelector('[data-w-dropdown-target="toggle"]');
    const dropdownElement = document.querySelector(
      '[data-controller="w-dropdown"]',
    );

    const mock = new Promise((resolve) => {
      document.addEventListener('w-dropdown:shown', (event) => {
        resolve(event);
      });
    });

    toggle.dispatchEvent(new Event('click'));

    const event = await mock;

    expect(event).toEqual(
      expect.objectContaining({
        type: 'w-dropdown:shown',
        target: dropdownElement,
      }),
    );
  });

  it('should support methods to show and hide the dropdown', async () => {
    expect(document.querySelectorAll('[role="tooltip"]')).toHaveLength(0);

    const dropdownElement = document.querySelector(
      '[data-controller="w-dropdown"]',
    );

    dropdownElement.dispatchEvent(new CustomEvent('custom:show'));

    expect(document.querySelectorAll('[role="tooltip"]')).toHaveLength(1);

    dropdownElement.dispatchEvent(new CustomEvent('custom:hide'));

    expect(document.querySelectorAll('[role="tooltip"]')).toHaveLength(0);
  });

  it('should support an offset value passed to tippy.js', async () => {
    application?.stop();
    document
      .querySelector('div')
      .setAttribute('data-w-dropdown-offset-value', '[12,24]');

    application = Application.start();
    application = Application.start();
    application.register('w-dropdown', DropdownController);

    await Promise.resolve();

    const tippy = application.getControllerForElementAndIdentifier(
      document.querySelector('div'),
      'w-dropdown',
    ).tippy;

    expect(tippy.props).toHaveProperty('offset', [12, 24]);
  });
});
