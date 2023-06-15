import { Application } from '@hotwired/stimulus';
import { DropdownController } from './DropdownController';

describe('DropdownController', () => {
  let application;

  beforeAll(() => {
    application?.stop();

    document.body.innerHTML = `
<div data-controller="w-dropdown">
  <button type="button" data-w-dropdown-target="toggle" aria-label="Actions"></button>
  <div data-w-dropdown-target="content">
    <a href="/">Option</a>
  </div>
</div>`;

    application = Application.start();
    application.register('w-dropdown', DropdownController);
  });

  it('initialises Tippy.js on connect', () => {
    const toggle = document.querySelector('[data-w-dropdown-target="toggle"]');
    const content = document.querySelector(
      '[data-w-dropdown-target="content"]',
    );
    expect(toggle.getAttribute('aria-expanded')).toBe('false');
    expect(content).toBe(null);
  });
});
