import { Application } from '@hotwired/stimulus';

import { FocusController } from './FocusController';

jest.useFakeTimers();

describe('FocusController', () => {
  let application;

  const setup = async (
    html = `<div>
    <a id="skip" class="button" data-controller="w-focus" data-action="click->w-focus#focus">Skip to main content</a>
    <main>Main content</main>
    <button id="other-content">other</button>
    </div>`,
    definition = {},
  ) => {
    document.body.innerHTML = `<main>${html}</main>`;

    application = Application.start();
    application.load({
      controllerConstructor: FocusController,
      identifier: 'w-focus',
      ...definition,
    });

    await Promise.resolve();
  };

  afterEach(() => {
    document.body.innerHTML = '';
    application.stop();
  });

  describe('skip to the main content on clicking the skip link', () => {
    beforeEach(async () => {
      await setup();
    });

    it('should keep tabindex, blur and focusout attribute as null when not in focus', () => {
      const mainElement = document.querySelector('main');

      expect(document.activeElement).toBe(document.body);
      expect(mainElement.getAttribute('tabindex')).toBe(null);
    });

    it('should skip to main when skip link is clicked', async () => {
      const mainElement = document.querySelector('main');

      document.getElementById('skip').click();

      await jest.runAllTimersAsync();

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

  describe('using to skip to a specific element', () => {
    beforeEach(async () => {
      await setup(
        `
    <main>
      <section>
        <div class="section-top"><h3>Section title</h3></div>
        <p>...lots of content...</p>
        <button
          type="button"
          data-controller="w-focus"
          data-action="w-focus#focus"
          data-w-focus-target-value=".section-top"
        >
          Skip to top
        </button>
      </section>
    </main>`,
        { identifier: 'w-focus' },
      );
    });

    it('should not have modified anything on connect', () => {
      const sectionTop = document.querySelector('.section-top');
      expect(sectionTop.getAttribute('tabindex')).toBe(null);
      expect(document.activeElement).toBe(document.body);
    });

    it('should focus on the section top when the button is clicked', async () => {
      expect(document.activeElement).toBe(document.body);

      const sectionTop = document.querySelector('.section-top');

      document.querySelector('button').click();

      await jest.runAllTimersAsync();

      expect(sectionTop.getAttribute('tabindex')).toEqual('-1');
      expect(document.activeElement).toBe(sectionTop);
    });

    it('should reset the attributes when focus is moved from the section top', () => {
      const sectionTop = document.querySelector('.section-top');

      const button = document.querySelector('button');
      button.focus();

      expect(document.activeElement).toBe(button);
      expect(sectionTop.getAttribute('tabindex')).toBe(null);
    });
  });

  describe('avoid modifying tabindex if not required', () => {
    beforeEach(async () => {
      await setup(
        `
    <main>
      <section>
        <div class="section-top" tabindex="-1"><h3>Section title</h3></div>
        <p>...lots of content...</p>
        <button
          type="button"
          data-controller="w-focus"
          data-action="w-focus#focus"
          data-w-focus-target-value=".section-top"
        >
          Skip to top
        </button>
      </section>
    </main>`,
        { identifier: 'w-focus' },
      );
    });

    it('should focus on the section top when the button is clicked & when focus is removed keep the tabindex', async () => {
      expect(document.activeElement).toBe(document.body);

      const sectionTop = document.querySelector('.section-top');

      document.querySelector('button').click();

      await jest.runAllTimersAsync();

      expect(sectionTop.getAttribute('tabindex')).toEqual('-1');
      expect(document.activeElement).toBe(sectionTop);

      document.querySelector('button').focus(); // move focus away
      sectionTop.dispatchEvent(new FocusEvent('focusout')); // simulate focusout event
      expect(document.activeElement).toBe(document.querySelector('button'));
      expect(sectionTop.getAttribute('tabindex')).toEqual('-1'); // tabindex should not be removed
    });
  });

  describe('focusing on an element that is added dynamically', () => {
    it('should support focusing on an element that is added dynamically', async () => {
      await setup(
        `
    <main>
      <button
        type="button"
        data-controller="w-focus"
        data-action="w-focus#focus"
        data-w-focus-target-value=".error-message"
      >
        Skip first error message
      </button>
      <section>
        <p>...lots of content...</p>
      </section>
    </main>`,
        { identifier: 'w-focus' },
      );

      expect(document.activeElement).toBe(document.body);

      const section = document.querySelector('section');
      const button = document.querySelector('button');

      button.click();
      await jest.runAllTimersAsync();

      // No element found, defaults to not changing focus
      expect(document.activeElement).toBe(document.body);

      const errorMessage = document.createElement('div');
      errorMessage.classList.add('error-message');
      section.appendChild(errorMessage);

      button.click();
      await jest.runAllTimersAsync();

      expect(document.activeElement).toBe(errorMessage);
    });
  });
});
