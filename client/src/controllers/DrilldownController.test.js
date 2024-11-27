import { Application } from '@hotwired/stimulus';
import { DrilldownController } from './DrilldownController';
import { DropdownController } from './DropdownController';
import { ActionController } from './ActionController';

jest.useFakeTimers();

describe('DrilldownController', () => {
  const eventNames = [];

  const events = {};
  let application;
  let errors = [];

  const setup = async (
    html = `
    <section>
      <div
        id="filters-drilldown"
        data-controller="w-drilldown"
        data-action='${[
          'w-swap:success@document->w-drilldown#updateCount',
          'w-dropdown:hide->w-drilldown#delayedClose',
          'w-dropdown:clickaway->w-drilldown#preventOutletClickaway',
        ].join(' ')}'
        data-w-drilldown-count-attr-value="data-w-active-filter-id"
      >
        <span data-w-drilldown-target="count"></span>
        <button type="button">Show filters</button>
        <div data-w-drilldown-target="menu" hidden>
          <h2>Filter by</h2>
          <button
            id="drilldown-toggle"
            type="button"
            aria-expanded="false"
            aria-controls="drilldown-field-0"
            data-action="click->w-drilldown#open"
            data-w-drilldown-target="toggle"
          >
            Field 1
          </button>
        </div>
        <div id="drilldown-field-0" hidden tabIndex="-1">
          <button type="button" data-action="click->w-drilldown#close">Back</button>
        </div>
      </div>
      <button type="button" id="action-element" data-controller="w-action">Action</button>
    </section>`,
    identifier = 'w-drilldown',
  ) => {
    document.body.innerHTML = `<main>${html}</main>`;

    application = new Application();
    application.handleError = (error, message) => {
      errors.push({ error, message });
    };
    application.register(identifier, DrilldownController);
    application.register('w-action', ActionController);
    application.register('w-dropdown', DropdownController);
    application.start();

    await jest.runAllTimersAsync();

    return [
      ...document.querySelectorAll(`[data-controller~="${identifier}"]`),
    ].map((element) =>
      application.getControllerForElementAndIdentifier(element, identifier),
    );
  };

  beforeEach(async () => {
    await setup();
  });

  afterEach(() => {
    application?.stop && application.stop();
    errors = [];
    eventNames.forEach((name) => {
      events[name] = [];
    });
  });

  describe('Opening & closing', () => {
    it('opens the submenu and sets active submenu value when toggle is clicked', async () => {
      const toggleButton = document.getElementById('drilldown-toggle');
      const submenu = document.getElementById('drilldown-field-0');

      toggleButton.click();
      await jest.runAllTimersAsync();

      expect(toggleButton.getAttribute('aria-expanded')).toBe('true');
      expect(submenu.hidden).toBeFalsy();
    });

    it('closes the submenu and clears active submenu value when close action is triggered', async () => {
      const toggleButton = document.getElementById('drilldown-toggle');
      const submenu = document.getElementById('drilldown-field-0');

      toggleButton.click();
      await jest.runAllTimersAsync();

      expect(submenu.hidden).toBeFalsy();

      const closeButton = document.querySelector(
        '[data-action="click->w-drilldown#close"]',
      );

      closeButton.click();
      await jest.runAllTimersAsync();

      expect(toggleButton.getAttribute('aria-expanded')).toBe('false');
      expect(submenu.hidden).toBeTruthy();
    });

    it('should close the menu when clicking outside the controlled area', async () => {
      const otherTrigger = document.createElement('button');
      otherTrigger.id = 'other-trigger';
      otherTrigger.type = 'button';
      otherTrigger.setAttribute('aria-controls', 'drilldown-field-0');
      document.body.appendChild(otherTrigger);

      const drilldownContainer = document.getElementById('filters-drilldown');
      const toggleButton = document.getElementById('drilldown-toggle');
      const submenu = document.getElementById('drilldown-field-0');

      toggleButton.click();
      await Promise.resolve();
      expect(submenu.hidden).toBeFalsy();

      let event = new CustomEvent('w-dropdown:clickaway', {
        detail: { target: document.getElementById('other-trigger') },
      });
      event.preventDefault = jest.fn();
      drilldownContainer.dispatchEvent(event);
      await jest.runAllTimersAsync();

      expect(event.preventDefault).toHaveBeenCalled();

      event = new CustomEvent('w-dropdown:clickaway', {
        detail: { target: document.getElementById('filters-drilldown') },
      });
      event.preventDefault = jest.fn();
      drilldownContainer.dispatchEvent(event);
      await jest.runAllTimersAsync();

      expect(event.preventDefault).not.toHaveBeenCalled();
    });

    it('should have the ability to be closed with a delay', async () => {
      const drilldownContainer = document.getElementById('filters-drilldown');
      const submenu = document.getElementById('drilldown-field-0');

      document.getElementById('drilldown-toggle').click();
      await Promise.resolve();
      expect(submenu.hidden).toBe(false);

      drilldownContainer.dispatchEvent(new Event('w-dropdown:hide'));
      await jest.advanceTimersByTimeAsync(180);
      expect(submenu.hidden).toBe(false);
      await jest.advanceTimersByTimeAsync(20);
      expect(submenu.hidden).toBe(true);
    });
  });

  describe('Action outlet connection & disconnection', () => {
    let actionElement;
    let openMock;

    beforeEach(() => {
      actionElement = document.createElement('div');
      actionElement.id = 'action-element';
      document.body.appendChild(actionElement);

      openMock = jest.fn();
      actionElement.addEventListener('click', openMock);
    });

    it('should add an event listener on outlet connection', async () => {
      actionElement.dispatchEvent(new Event('connection'));
      actionElement.click();
      expect(openMock).toHaveBeenCalled();
    });

    it('should remove event listener on outlet disconnection', async () => {
      actionElement.dispatchEvent(new Event('connection'));

      actionElement.click();
      expect(openMock).toHaveBeenCalledTimes(1);

      actionElement.removeEventListener('click', openMock);
      actionElement.click();
      expect(openMock).toHaveBeenCalledTimes(1);
    });
  });

  describe('Updating counts', () => {
    beforeEach(async () => {
      await setup(`<section>
        <div id="filters-drilldown" data-controller="w-drilldown" data-w-drilldown-count-attr-value="data-w-active-filter-id" data-action="stimulus-reflex:success->w-drilldown#updateCount">
          <span data-w-drilldown-target="count"></span>
          <span data-w-drilldown-target="count" data-count-name="field-0"></span>
          <div data-w-active-filter-id="field-0"></div>
          <div data-w-active-filter-id="field-1"></div>
          <div data-w-active-filter-id="field-0"></div>
        </div>
      </section>`);
    });

    it('updates the count target text and visibility based on data-w-active-filter-id', () => {
      const countTargets = document.querySelectorAll(
        '[data-w-drilldown-target="count"]',
      );

      expect(countTargets[0].textContent).toBe('3');
      expect(countTargets[0].hidden).toBe(false);

      expect(countTargets[1].textContent).toBe('2');
      expect(countTargets[1].hidden).toBe(false);
    });
  });
});
