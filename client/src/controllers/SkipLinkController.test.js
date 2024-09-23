import { Application } from '@hotwired/stimulus';

import { SkipLinkController } from './SkipLinkController';

describe('skip to the main content on clicking the skiplink', () => {
  document.body.innerHTML = `
  <a id="skip" class="button" data-controller="w-skip-link" data-action="click->w-skip-link#skip">Skip to main content</a>
  <main>Main content</main>
  <button id="other-content">other</button>`;

  const application = Application.start();

  application.register('w-skip-link', SkipLinkController);

  const mainElement = document.querySelector('main');

  it('should keep tabindex, blur and focusout attribute as null when not in focus', () => {
    expect(document.activeElement).toBe(document.body);
    expect(mainElement.getAttribute('tabindex')).toBe(null);
  });

  it('should skip to main when skip link is clicked', () => {
    document.getElementById('skip').click();
    expect(mainElement.getAttribute('tabindex')).toEqual('-1');
    expect(document.activeElement).toBe(mainElement);
    expect(mainElement.getAttribute('blur')).toBe(null);
    expect(mainElement.getAttribute('focusout')).toBe(null);
  });

  it('should reset tab index when focus is moved from skip link', () => {
    const otherContent = document.getElementById('other-content');
    otherContent.focus();
    expect(document.activeElement).toBe(otherContent);
    expect(otherContent.getAttribute('tabindex')).toBe(null);
    expect(otherContent.getAttribute('blur')).toBe(null);
    expect(otherContent.getAttribute('focusout')).toBe(null);
  });
});
