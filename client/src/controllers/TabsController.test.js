import { setImmediate } from 'timers';
import { Application } from '@hotwired/stimulus';
import { TabsController } from './TabsController';

function simulateKeydown(key) {
  const event = new KeyboardEvent('keydown', {
    key,
    code: key,
    bubbles: true,
    cancelable: true,
  });
  document.activeElement.dispatchEvent(event);
}

jest.useFakeTimers();

const flushPromises = () => new Promise(setImmediate);

describe('TabsController', () => {
  const eventNames = ['w-tabs:changed', 'w-tabs:ready', 'w-tabs:selected'];
  const oldWindowLocation = window.location;

  let application;
  let errors = [];
  let events = {};

  const setup = async (
    html = `
    <div id="test-tabs" data-controller="w-tabs" data-action="custom:event->w-tabs#select" data-w-tabs-active-class="animate-in">
      <div role="tablist" data-action="keydown.right->w-tabs#selectNext keydown.left->w-tabs#selectPrevious keydown.home->w-tabs#selectFirst keydown.end->w-tabs#selectLast">
        <a id="tab-1" href="#tab-panel-1" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent">
          Cheese
        </a>
        <a id="tab-2" href="#tab-panel-2" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent">
          Chocolate
        </a>
        <a id="tab-3" href="#tab-panel-3" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent">
          Coffee
        </a>
      </div>
      <div class="tab-content">
        <section class="panel" id="tab-panel-1" role="tabpanel" aria-labelledby="tab-1" data-w-tabs-target="panel" data-action="w-focus:focus->w-tabs#selectInside">
          All about <a href="/cheese">cheese</a>.
          <a href="#tab-panel-3" id="extra-trigger-inside" type="button" data-action="w-tabs#select:prevent" data-w-tabs-focus-param="true" data-w-tabs-target="trigger">Inside tab trigger for Tab 3 as link</a>
        </section>
        <section class="panel" id="tab-panel-2" role="tabpanel" aria-labelledby="tab-2" data-w-tabs-target="panel" data-action="w-focus:focus->w-tabs#selectInside">
          All about <a href="/chocolate">chocolate</a>.
        </section>
        <section class="panel" id="tab-panel-3" role="tabpanel" aria-labelledby="tab-3" data-w-tabs-target="panel" data-action="w-focus:focus->w-tabs#selectInside">
          All about <a href="/coffee">coffee</a>.
        </section>
      </div>
      <button id="extra-trigger" type="button" data-action="w-tabs#select" data-w-tabs-target="trigger" data-w-tabs-focus-param="true" data-w-tabs-id-param="tab-panel-2">Outside trigger for Tab 2 as button</button>
    </div>
  `,
    definitions = [
      { identifier: 'w-tabs', controllerConstructor: TabsController },
    ],
  ) => {
    document.body.innerHTML = `<main>${html}</main>`;
    application = Application.start();
    application.handleError = (error, message) => {
      errors.push({ error, message });
    };
    application.load(...definitions);
    await Promise.resolve();
  };

  beforeAll(() => {
    eventNames.forEach((name) => {
      document.addEventListener(name, (event) => {
        if (!events[name]) {
          events[name] = [];
        }
        events[name].push(event);
      });
    });
  });

  afterEach(() => {
    application?.stop();
    jest.clearAllMocks();
    errors = [];
    events = {};

    delete window.location;

    window.location = Object.defineProperties(
      {},
      {
        ...Object.getOwnPropertyDescriptors(oldWindowLocation),
        assign: { configurable: true, value: jest.fn() },
      },
    );
  });

  describe('tabs behavior', () => {
    it('should load with an initial default tab & dispatch `ready`', async () => {
      await setup();
      expect(errors).toHaveLength(0);

      const [tab1, tab2, tab3] =
        document.querySelector('[role="tablist"]').children;

      const [tab1Panel, tab2Panel, tab3Panel] =
        document.querySelector('.tab-content').children;

      // default should be to have the first tab selected

      expect(tab1.getAttribute('aria-selected')).toBe('true');
      expect(tab1Panel.hidden).toBeFalsy();
      expect(tab2Panel.hidden).toBeTruthy();
      expect(tab3Panel.hidden).toBeTruthy();

      // ensure aria-controls are set correctly

      expect(tab1.getAttribute('aria-controls')).toBe('tab-panel-1');
      expect(tab2.getAttribute('aria-controls')).toBe('tab-panel-2');
      expect(tab3.getAttribute('aria-controls')).toBe('tab-panel-3');

      // ensure tabindex is set correctly

      expect(tab1.getAttribute('tabindex')).toBe('0');
      expect(tab2.getAttribute('tabindex')).toBe('-1');
      expect(tab3.getAttribute('tabindex')).toBe('-1');

      // do not change the tabindex of the extra triggers
      expect(
        document
          .getElementById('extra-trigger-inside')
          .hasAttribute('tabindex'),
      ).toBe(false);
      expect(
        document.getElementById('extra-trigger').hasAttribute('tabindex'),
      ).toBe(false);

      // fires the correct events

      expect(events['w-tabs:ready']).toHaveProperty(
        '0.detail.current',
        'tab-panel-1',
      );

      expect(events['w-tabs:changed'] || []).toHaveLength(0);
      expect(events['w-tabs:selected'] || []).toHaveLength(1);
    });

    it('should support changing tabs with clicks and changing classes', async () => {
      await setup();
      expect(errors).toHaveLength(0);

      const [tab1, tab2, tab3] =
        document.querySelector('[role="tablist"]').children;
      const [tab1Panel, tab2Panel, tab3Panel] =
        document.querySelector('.tab-content').children;

      expect(tab2Panel.className).toEqual('panel');

      tab2.click();
      await jest.runAllTimersAsync();

      expect(tab1.getAttribute('aria-selected')).toBe(null);
      expect(tab2.getAttribute('aria-selected')).toBe('true');

      expect(tab1Panel.hidden).toBeTruthy();
      expect(tab2Panel.hidden).toBeFalsy();
      expect(tab2Panel.className).toEqual('panel animate-in');

      // ensure tabindex is set correctly

      expect(tab1.getAttribute('tabindex')).toBe('-1');
      expect(tab2.getAttribute('tabindex')).toBe('0');
      expect(tab3.getAttribute('tabindex')).toBe('-1');

      // do not change the tabindex of the extra triggers
      expect(
        document
          .getElementById('extra-trigger-inside')
          .hasAttribute('tabindex'),
      ).toBe(false);
      expect(
        document.getElementById('extra-trigger').hasAttribute('tabindex'),
      ).toBe(false);

      // fires the correct events
      expect(events['w-tabs:changed']).toHaveLength(1);
      expect(events['w-tabs:changed']).toHaveProperty('0.detail', {
        current: 'tab-panel-2',
        previous: 'tab-panel-1',
        tabs: document.getElementById('test-tabs'),
      });

      const tabs = document.getElementById('test-tabs');

      expect(
        events['w-tabs:selected'].map((event) => ({
          ...event.detail,
          targetId: event.target.id,
        })),
      ).toEqual([
        {
          current: 'tab-panel-1',
          previous: '',
          tabs,
          targetId: 'tab-1',
        },
        {
          current: 'tab-panel-2',
          previous: 'tab-panel-1',
          tabs,
          targetId: 'tab-2',
        },
        // important: also fires for the extra-trigger button (as it controls the same panel)
        {
          current: 'tab-panel-2',
          previous: 'tab-panel-1',
          tabs,
          targetId: 'extra-trigger',
        },
      ]);
    });

    it('should support non-tab triggers (inside tab panels)', async () => {
      await setup();
      expect(errors).toHaveLength(0);

      const [tab1, tab2, tab3] =
        document.querySelector('[role="tablist"]').children;
      const [tab1Panel, tab2Panel, tab3Panel] =
        document.querySelector('.tab-content').children;

      expect(tab2Panel.hidden).toBeTruthy();

      const trigger = document.getElementById('extra-trigger-inside');

      trigger.click();
      await jest.runAllTimersAsync();

      expect(tab1.getAttribute('aria-selected')).toBe(null);
      expect(tab2.getAttribute('aria-selected')).toBe(null);
      expect(tab3.getAttribute('aria-selected')).toBe('true');

      expect(tab1Panel.hidden).toBeTruthy();
      expect(tab2Panel.hidden).toBeTruthy();
      expect(tab3Panel.hidden).toBeFalsy();

      // focus should be on the selected tab
      expect(document.activeElement).toBe(tab3);
    });

    it('should support non-tab triggers (outside tab panels)', async () => {
      await setup();
      expect(errors).toHaveLength(0);

      const [tab1, tab2, tab3] =
        document.querySelector('[role="tablist"]').children;
      const [tab1Panel, tab2Panel, tab3Panel] =
        document.querySelector('.tab-content').children;

      expect(tab2Panel.hidden).toBeTruthy();

      const trigger = document.getElementById('extra-trigger');

      trigger.click();
      await jest.runAllTimersAsync();

      expect(tab1.getAttribute('aria-selected')).toBe(null);
      expect(tab2.getAttribute('aria-selected')).toBe('true');
      expect(tab3.getAttribute('aria-selected')).toBe(null);

      expect(tab1Panel.hidden).toBeTruthy();
      expect(tab2Panel.hidden).toBeFalsy();
      expect(tab3Panel.hidden).toBeTruthy();

      // focus should be on the selected tab
      expect(document.activeElement).toBe(tab2);
    });

    it('should support event handling for ad-hoc selection via action/events', async () => {
      await setup();
      expect(errors).toHaveLength(0);

      const [tab1, tab2] = document.querySelector('[role="tablist"]').children;
      const [tab1Panel, tab2Panel, tab3Panel] =
        document.querySelector('.tab-content').children;

      expect(tab1.getAttribute('aria-selected')).toBe('true');

      const tabsElement = document.getElementById('test-tabs');

      tabsElement.dispatchEvent(
        new CustomEvent('custom:event', {
          detail: { id: 'tab-panel-2' },
        }),
      );

      await jest.runAllTimersAsync();

      expect(tab1.getAttribute('aria-selected')).toBe(null);
      expect(tab2.getAttribute('aria-selected')).toBe('true');
      expect(tab1Panel.hidden).toBeTruthy();
      expect(tab2Panel.hidden).toBeFalsy();
    });

    it('should gracefully handle the select method without a found panelId', async () => {
      await setup();
      expect(errors).toHaveLength(0);
      expect(events['w-tabs:selected']).toHaveLength(1);
      expect(
        document.getElementById('tab-1').getAttribute('aria-selected'),
      ).toBe('true');
      expect(document.getElementById('tab-panel-1').hidden).toBeFalsy();

      // dispatch an event that has no id in it
      const tabsElement = document.getElementById('test-tabs');
      tabsElement.dispatchEvent(new CustomEvent('custom:event'));

      await jest.runAllTimersAsync();

      // check no errors or changes to the selected tab
      expect(errors).toHaveLength(0);
      expect(events['w-tabs:selected']).toHaveLength(1);
      expect(
        document.getElementById('tab-1').getAttribute('aria-selected'),
      ).toBe('true');
      expect(document.getElementById('tab-panel-1').hidden).toBeFalsy();
    });

    it('should gracefully handle the select method with an invalid panelId', async () => {
      await setup();
      expect(errors).toHaveLength(0);
      expect(events['w-tabs:selected']).toHaveLength(1);
      expect(
        document.getElementById('tab-1').getAttribute('aria-selected'),
      ).toBe('true');
      expect(document.getElementById('tab-panel-1').hidden).toBeFalsy();

      // dispatch an event that has no valid panel id in it
      const tabsElement = document.getElementById('test-tabs');
      tabsElement.dispatchEvent(
        new CustomEvent('custom:event', {
          detail: { id: 'not-a-panel' },
        }),
      );

      await jest.runAllTimersAsync();

      // check no errors or changes to the selected tab
      expect(errors).toHaveLength(0);
      expect(events['w-tabs:selected']).toHaveLength(1);
      expect(
        document.getElementById('tab-1').getAttribute('aria-selected'),
      ).toBe('true');
      expect(document.getElementById('tab-panel-1').hidden).toBeFalsy();
    });

    it('should support selection via an event dispatched from inside the tab panel', async () => {
      await setup();

      const [tab1, tab2, tab3] = document.querySelectorAll('[role="tab"]');
      const [tab1Panel, tab2Panel, tab3Panel] =
        document.querySelectorAll('section');

      expect(tab1.getAttribute('aria-selected')).toBe('true');

      // dispatch an event from inside the third tab panel to select the third tab
      tab3Panel
        .querySelector('a')
        .dispatchEvent(new CustomEvent('w-focus:focus', { bubbles: true }));

      await jest.runAllTimersAsync();

      expect(tab1.getAttribute('aria-selected')).toBe(null);
      expect(tab2.getAttribute('aria-selected')).toBe(null);
      expect(tab3.getAttribute('aria-selected')).toBe('true');

      // dispatch an event from inside the second tab panel to select the second tab
      tab2Panel
        .querySelector('a')
        .dispatchEvent(new CustomEvent('w-focus:focus', { bubbles: true }));

      await jest.runAllTimersAsync();

      expect(tab1.getAttribute('aria-selected')).toBe(null);
      expect(tab2.getAttribute('aria-selected')).toBe('true');
      expect(tab3.getAttribute('aria-selected')).toBe(null);
    });

    it('should gracefully handle adding panel/trigger targets', async () => {
      await setup(`
      <div id="mutating-tabs" data-controller="w-tabs">
        <div role="tablist">
          <a id="tab-1" href="#tab-panel-1" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent">A</a>
          <a id="tab-2" href="#tab-panel-2" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent">B</a>
        </div>
        <section id="tab-panel-1" role="tabpanel" aria-labelledby="tab-1" data-w-tabs-target="panel">A (content)</section>
        <section id="tab-panel-2" role="tabpanel" aria-labelledby="tab-2" data-w-tabs-target="panel">B (content)</section>
      </div>
    `);

      expect(errors).toHaveLength(0);

      const [tab1, tab2] = document.querySelectorAll('[role="tab"]');
      const [tab1Panel, tab2Panel] = document.querySelectorAll('section');

      expect(tab1.getAttribute('aria-selected')).toBe('true');
      expect(tab1Panel.hidden).toBeFalsy();

      // add a new tab & panel

      const newTab = document.createElement('a');
      newTab.id = 'tab-3';
      newTab.setAttribute('href', '#tab-panel-3');
      newTab.setAttribute('role', 'tab');
      newTab.setAttribute('data-w-tabs-target', 'trigger');
      newTab.setAttribute('data-action', 'w-tabs#select:prevent');
      newTab.textContent = 'C';

      const newPanel = document.createElement('section');
      newPanel.id = 'tab-panel-3';
      newPanel.setAttribute('role', 'tabpanel');
      newPanel.setAttribute('aria-labelledby', 'tab-3');
      newPanel.setAttribute('data-w-tabs-target', 'panel');
      newPanel.textContent = 'C (content)';

      document.querySelector('[role="tablist"]').appendChild(newTab);
      document.getElementById('mutating-tabs').appendChild(newPanel);

      await jest.runAllTimersAsync();

      expect(errors).toHaveLength(0);

      // check the new tab can be selected

      const tab3New = document.getElementById('tab-3');
      tab3New.click();

      await jest.runAllTimersAsync();

      expect(tab1.getAttribute('aria-selected')).toBe(null);
      expect(tab2.getAttribute('aria-selected')).toBe(null);
      expect(tab3New.getAttribute('aria-selected')).toBe('true');
      expect(tab1Panel.hidden).toBeTruthy();
      expect(tab2Panel.hidden).toBeTruthy();
    });

    it('should gracefully handle removal of panel/trigger targets', async () => {
      await setup(`
      <div id="mutating-tabs" data-controller="w-tabs">
        <div role="tablist">
          <a id="tab-1" href="#tab-panel-1" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent">A</a>
          <a id="tab-2" href="#tab-panel-2" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent">B</a>
          <a id="tab-3" href="#tab-panel-3" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent" aria-selected="true">C</a>
        </div>
        <section id="tab-panel-1" role="tabpanel" aria-labelledby="tab-1" data-w-tabs-target="panel">A (content)</section>
        <section id="tab-panel-2" role="tabpanel" aria-labelledby="tab-2" data-w-tabs-target="panel">B (content)</section>
        <section id="tab-panel-3" role="tabpanel" aria-labelledby="tab-3" data-w-tabs-target="panel">C (content)</section>
      </div>
    `);

      expect(errors).toHaveLength(0);

      const [tab1, tab2, tab3] = document.querySelectorAll('[role="tab"]');
      const [tab1Panel, tab2Panel, tab3Panel] =
        document.querySelectorAll('section');

      expect(tab1.getAttribute('aria-selected')).toBe(null);
      expect(tab3.getAttribute('aria-selected')).toBe('true');
      expect(tab1Panel.hidden).toBeTruthy();
      expect(tab3Panel.hidden).toBeFalsy();

      // remove the second tab & panel

      tab2.remove();
      tab2Panel.remove();

      await jest.runAllTimersAsync();

      expect(errors).toHaveLength(0);

      // check that other tabs can still be selected

      tab1.click();

      await jest.runAllTimersAsync();

      expect(tab1.getAttribute('aria-selected')).toBe('true');
      expect(tab3.getAttribute('aria-selected')).toBe(null);
      expect(tab1Panel.hidden).toBeFalsy();
      expect(tab3Panel.hidden).toBeTruthy();
    });
  });

  describe('handling transitions', () => {
    it('should allow for animated transition durations', async () => {
      await setup(/* html */ `
    <style>
      [data-w-tabs-active-class~='animate-in'] [data-w-tabs-target='panel'] {
        transition-behavior: allow-discrete;
        transition-property: opacity display;
        /* JSDOM's getComputedStyle always gives the value as-is,
           but browsers always normalize them to seconds */
        transition-delay: 0.1s;
        transition-duration: 0.3s;
        transition-timing-function: ease-in-out;
        opacity: 0;
      }
      [data-w-tabs-active-class~='animate-in'] [data-w-tabs-target='panel'].animate-in {
        opacity: 1;
      }
    </style>
    <div id="basic-tabs" data-controller="w-tabs" data-w-tabs-active-class="animate-in">
      <div role="tablist">
        <a id="tab-1" href="#tab-panel-1" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent">A</a>
        <a id="tab-2" href="#tab-panel-2" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent">B</a>
        <a id="tab-3" href="#tab-panel-3" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent">C</a>
      </div>
      <section id="tab-panel-1" role="tabpanel" aria-labelledby="tab-1" data-w-tabs-target="panel">A (content)</section>
      <section id="tab-panel-2" role="tabpanel" aria-labelledby="tab-2" data-w-tabs-target="panel">B (content)</section>
      <section id="tab-panel-3" role="tabpanel" aria-labelledby="tab-3" data-w-tabs-target="panel">C (content)</section>
    </div>
  `);

      expect(errors).toHaveLength(0);

      const [tab1, tab2, tab3] = document.querySelectorAll('[role="tab"]');
      const [tab1Panel, tab2Panel, tab3Panel] =
        document.querySelectorAll('section');

      // it should animate (with transitions) on load

      expect(tab1.getAttribute('aria-selected')).toBe('true');
      expect(tab2.getAttribute('aria-selected')).toBe(null);
      expect(tab1Panel.className).toEqual(''); // not set until after animation
      expect(tab2Panel.className).toEqual('');
      expect(tab1Panel.hidden).toBeFalsy();
      expect(tab2Panel.hidden).toBeTruthy();

      await jest.runAllTimersAsync();

      expect(tab1Panel.className).toEqual('animate-in');

      // now switch to the second tab & check handling of transition events

      tab2.click();

      await Promise.resolve(); // intentionally not running timers

      expect(tab1.getAttribute('aria-selected')).toBe(null);
      expect(tab2.getAttribute('aria-selected')).toBe('true');
      expect(tab1Panel.className).toEqual(''); // class instantly removed
      expect(tab2Panel.className).toEqual('');
      expect(tab1Panel.hidden).toBeFalsy(); // still visible until transition ends
      expect(tab2Panel.hidden).toBeTruthy();

      tab1Panel.dispatchEvent(new Event('transitionend', { bubbles: true }));

      await flushPromises(); // intentionally not running timers, but waiting for the transitionend event

      // Should set and remove the hidden attribute accordingly
      expect(tab1Panel.hidden).toBeTruthy();
      expect(tab2Panel.hidden).toBeFalsy();
      // But the class should not change until the next transition
      expect(tab1Panel.className).toEqual('');
      expect(tab2Panel.className).toEqual('');

      tab2Panel.dispatchEvent(new Event('transitionend', { bubbles: true }));

      await flushPromises(); // intentionally not running timers, but waiting for the transitionend event

      expect(tab1Panel.hidden).toBeTruthy();
      expect(tab2Panel.hidden).toBeFalsy();

      expect(tab1Panel.className).toEqual('');
      expect(tab2Panel.className).toEqual('animate-in');

      // select tab 3 and check that the max timeout (transition value) is respected

      tab3.click();

      await Promise.resolve(); // intentionally not running timers

      expect(tab2.getAttribute('aria-selected')).toBe(null);
      expect(tab3.getAttribute('aria-selected')).toBe('true');
      expect(tab2Panel.className).toEqual(''); // class instantly removed
      expect(tab3Panel.className).toEqual(''); // new class not yet set
      expect(tab2Panel.hidden).toBeFalsy(); // still visible until transition ends
      expect(tab3Panel.hidden).toBeTruthy();

      // run timers to 350ms first, check no change

      jest.advanceTimersByTime(350);
      await flushPromises();

      expect(tab2Panel.className).toEqual('');
      expect(tab3Panel.className).toEqual(''); // new class not yet set
      expect(tab2Panel.hidden).toBeFalsy(); // still visible until transition ends
      expect(tab3Panel.hidden).toBeTruthy();

      // run timers for 50ms (now 400ms), check hidden attribute applied

      jest.advanceTimersByTime(50);
      await flushPromises();

      expect(tab2Panel.hidden).toBeTruthy(); // previous panel now hidden
      expect(tab3Panel.hidden).toBeFalsy(); // new panel now visible
      expect(tab2Panel.className).toEqual('');
      expect(tab3Panel.className).toEqual(''); // new class not yet set

      // run timers for another 350ms (now 750ms), check no change

      jest.advanceTimersByTime(350);
      await flushPromises();

      expect(tab2Panel.hidden).toBeTruthy(); // previous panel now hidden
      expect(tab3Panel.hidden).toBeFalsy(); // new panel now visible
      expect(tab2Panel.className).toEqual('');
      expect(tab3Panel.className).toEqual(''); // new class not yet set

      // run timers for 50ms (now 800ms), check transition class added

      jest.advanceTimersByTime(50);
      await flushPromises();

      expect(tab2Panel.hidden).toBeTruthy(); // previous panel now hidden
      expect(tab3Panel.hidden).toBeFalsy(); // new panel now visible
      expect(tab2Panel.className).toEqual('');
      expect(tab3Panel.className).toEqual('animate-in'); // new class set
    });
  });

  describe('leveraging keyboard events', () => {
    it('should allow switching between tabs using the keyboard', async () => {
      await setup();
      expect(errors).toHaveLength(0);

      const [tab1, tab2, tab3] =
        document.querySelector('[role="tablist"]').children;
      const [tab1Panel, tab2Panel, tab3Panel] =
        document.querySelector('.tab-content').children;

      // check initial state with first tab selected

      expect(tab1.getAttribute('aria-selected')).toBe('true');
      expect(tab2Panel.hidden).toBeTruthy();
      expect(tab3Panel.hidden).toBeTruthy();

      // ensure tabindex is set correctly

      expect([tab1, tab2, tab3].map((_) => _.getAttribute('tabindex'))).toEqual(
        ['0', '-1', '-1'],
      );

      // switch to the second tab using the right arrow key

      tab1.focus();
      simulateKeydown('ArrowRight');
      await jest.runAllTimersAsync();

      expect(tab2.getAttribute('aria-selected')).toBe('true');
      expect(tab2).toBe(document.activeElement);
      expect(tab1Panel.hidden).toBeTruthy();
      expect(tab2Panel.hidden).toBeFalsy();

      // ensure tabindex is set correctly

      expect([tab1, tab2, tab3].map((_) => _.getAttribute('tabindex'))).toEqual(
        ['-1', '0', '-1'],
      );

      // switch back to the first tab using the left arrow key

      tab2.focus();
      simulateKeydown('ArrowLeft');
      await jest.runAllTimersAsync();

      expect(tab1.getAttribute('aria-selected')).toBe('true');
      expect(tab1).toBe(document.activeElement);
      expect(tab2Panel.hidden).toBeTruthy();
      expect(tab1Panel.hidden).toBeFalsy();

      // switch to the last tab tab using the left arrow key again (if on the first)

      simulateKeydown('ArrowLeft');
      await jest.runAllTimersAsync();

      expect(tab3.getAttribute('aria-selected')).toBe('true');

      // ensure tabindex is set correctly

      expect([tab1, tab2, tab3].map((_) => _.getAttribute('tabindex'))).toEqual(
        ['-1', '-1', '0'],
      );

      // using the right arrow key should now go back to the first tab again

      simulateKeydown('ArrowRight');
      await jest.runAllTimersAsync();

      expect(tab1.getAttribute('aria-selected')).toBe('true');

      expect([tab1, tab2, tab3].map((_) => _.getAttribute('tabindex'))).toEqual(
        ['0', '-1', '-1'],
      );
    });

    it('should allow switching to the first or last tabs using the keyboard', async () => {
      await setup();
      expect(errors).toHaveLength(0);

      const [tab1, tab2, tab3] =
        document.querySelector('[role="tablist"]').children;
      const [tab1Panel, tab2Panel, tab3Panel] =
        document.querySelector('.tab-content').children;

      // check initial state with first tab selected

      expect(tab1.getAttribute('aria-selected')).toBe('true');
      expect(tab2Panel.hidden).toBeTruthy();
      expect(tab3Panel.hidden).toBeTruthy();

      // first use 'end' to go to the last tab

      tab1.focus();
      simulateKeydown('End');
      await jest.runAllTimersAsync();

      expect(tab3.getAttribute('aria-selected')).toBe('true');
      expect(tab3).toBe(document.activeElement);
      expect(tab1Panel.hidden).toBeTruthy();
      expect(tab3Panel.hidden).toBeFalsy();

      // ensure tabindex is set correctly

      expect([tab1, tab2, tab3].map((_) => _.getAttribute('tabindex'))).toEqual(
        ['-1', '-1', '0'],
      );

      // now use 'home' to go back to the first tab

      tab2.focus();
      simulateKeydown('Home');

      await jest.runAllTimersAsync();

      expect(tab1.getAttribute('aria-selected')).toBe('true');
      expect(tab1).toBe(document.activeElement);
      expect(tab3Panel.hidden).toBeTruthy();
      expect(tab1Panel.hidden).toBeFalsy();

      // ensure tabindex is set correctly

      expect([tab1, tab2, tab3].map((_) => _.getAttribute('tabindex'))).toEqual(
        ['0', '-1', '-1'],
      );
    });
  });

  describe('allowing for default tab selection based on the DOM', () => {
    it('should allow for declaring the active panel id via a Stimulus value', async () => {
      await setup(`
    <div id="basic-tabs" data-controller="w-tabs" data-w-tabs-active-panel-id-value="tab-panel-3">
      <div role="tablist">
        <a id="tab-1" href="#tab-panel-1" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent">A</a>
        <a id="tab-2" href="#tab-panel-2" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent">B</a>
        <a id="tab-3" href="#tab-panel-3" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent">C</a>
      </div>
      <section id="tab-panel-1" role="tabpanel" aria-labelledby="tab-1" data-w-tabs-target="panel">A (content)</section>
      <section id="tab-panel-2" role="tabpanel" aria-labelledby="tab-2" data-w-tabs-target="panel">B (content)</section>
      <section id="tab-panel-3" role="tabpanel" aria-labelledby="tab-3" data-w-tabs-target="panel">C (content)</section>
    </div>
  `);
      expect(errors).toHaveLength(0);

      const [tab1, tab2, tab3] =
        document.querySelector('[role="tablist"]').children;
      const [tab1Panel, tab2Panel, tab3Panel] =
        document.querySelectorAll('section');

      expect(tab1.getAttribute('aria-selected')).toBe(null);
      expect(tab3.getAttribute('aria-selected')).toBe('true');
      expect(tab1Panel.hidden).toBeTruthy();
      expect(tab2Panel.hidden).toBeTruthy();
      expect(tab3Panel.hidden).toBeFalsy();

      // ensure tabindex is set correctly

      expect([tab1, tab2, tab3].map((_) => _.getAttribute('tabindex'))).toEqual(
        ['-1', '-1', '0'],
      );

      expect(events['w-tabs:ready']).toHaveProperty(
        '0.detail.current',
        'tab-panel-3',
      );
    });

    it('should allow for declaring the active panel id aria-selected on a tab', async () => {
      await setup(`
    <div id="basic-tabs" data-controller="w-tabs">
      <div role="tablist">
        <a id="tab-1" href="#tab-panel-1" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent">A</a>
        <a id="tab-2" href="#tab-panel-2" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent" aria-selected="true">B</a>
        <a id="tab-3" href="#tab-panel-3" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent">C</a>
      </div>
      <section id="tab-panel-1" role="tabpanel" aria-labelledby="tab-1" data-w-tabs-target="panel">A (content)</section>
      <section id="tab-panel-2" role="tabpanel" aria-labelledby="tab-2" data-w-tabs-target="panel">B (content)</section>
      <section id="tab-panel-3" role="tabpanel" aria-labelledby="tab-3" data-w-tabs-target="panel">C (content)</section>
    </div>
  `);
      expect(errors).toHaveLength(0);

      const [tab1, tab2, tab3] = document.querySelectorAll('[role="tab"]');
      const [tab1Panel, tab2Panel, tab3Panel] =
        document.querySelectorAll('section');

      expect(tab1.getAttribute('aria-selected')).toBe(null);
      expect(tab2.getAttribute('aria-selected')).toBe('true');
      expect(tab3.getAttribute('aria-selected')).toBe(null);
      expect(tab1Panel.hidden).toBeTruthy();
      expect(tab2Panel.hidden).toBeFalsy();
      expect(tab3Panel.hidden).toBeTruthy();

      // ensure tabindex is set correctly

      expect([tab1, tab2, tab3].map((_) => _.getAttribute('tabindex'))).toEqual(
        ['-1', '0', '-1'],
      );

      expect(events['w-tabs:ready']).toHaveProperty(
        '0.detail.current',
        'tab-panel-2',
      );
    });
  });

  describe('using history & browser location to sync selected tabs', () => {
    it('should not update the location & history on load but only on subsequent tab changes', async () => {
      expect(window.location.toString()).toEqual('http://localhost/');

      await setup(`
        <div id="location-tabs" data-controller="w-tabs" data-action="popstate@window->w-tabs#select" data-w-tabs-use-location-value="true">
          <div role="tablist">
            <a id="tab-1" href="#tab-panel-1" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent">A</a>
            <a id="tab-2" href="#tab-panel-2" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent" aria-selected="true">B</a>
            <a id="tab-3" href="#tab-panel-3" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent">C</a>
          </div>
          <section id="tab-panel-1" role="tabpanel" aria-labelledby="tab-1" data-w-tabs-target="panel">A (content)</section>
          <section id="tab-panel-2" role="tabpanel" aria-labelledby="tab-2" data-w-tabs-target="panel">B (content)</section>
          <section id="tab-panel-3" role="tabpanel" aria-labelledby="tab-3" data-w-tabs-target="panel">C (content)</section>
        </div>
      `);
      expect(errors).toHaveLength(0);

      const [tab1, tab2, tab3] = document.querySelectorAll('[role="tab"]');
      const [tab1Panel, tab2Panel, tab3Panel] =
        document.querySelectorAll('section');

      // avoid updating hash on initial load
      expect(tab2.getAttribute('aria-selected')).toBe('true');
      expect(tab1Panel.hidden).toBeTruthy();
      expect(tab2Panel.hidden).toBeFalsy();
      expect(window.location.toString()).toEqual('http://localhost/');
      expect(window.history.state).toEqual(null);

      // ensure tabindex is set correctly

      expect([tab1, tab2, tab3].map((_) => _.getAttribute('tabindex'))).toEqual(
        ['-1', '0', '-1'],
      );

      // select the first tab, check the URL syncs & history is updated

      tab1.click();
      await jest.runAllTimersAsync();
      expect(window.location.toString()).toEqual(
        'http://localhost/#tab-panel-1',
      );
      expect(window.history.state).toEqual({
        'w-tabs-panel-id': 'tab-panel-1',
      });

      // check DOM state is correct
      expect(tab1.getAttribute('aria-selected')).toBe('true');
      expect(tab1Panel.hidden).toBeFalsy(); // visible
      expect(tab2Panel.hidden).toBeTruthy();
      expect(tab3Panel.hidden).toBeTruthy();

      // ensure tabindex is set correctly

      expect([tab1, tab2, tab3].map((_) => _.getAttribute('tabindex'))).toEqual(
        ['0', '-1', '-1'],
      );

      // select the third tab, check the URL syncs & history is updated

      tab3.click();
      await jest.runAllTimersAsync();
      expect(window.location.toString()).toEqual(
        'http://localhost/#tab-panel-3',
      );
      expect(window.history.state).toEqual({
        'w-tabs-panel-id': 'tab-panel-3',
      });

      // check DOM state is correct
      expect(tab3.getAttribute('aria-selected')).toBe('true');
      expect(tab1Panel.hidden).toBeTruthy();
      expect(tab2Panel.hidden).toBeTruthy();
      expect(tab3Panel.hidden).toBeFalsy(); // visible

      // now use browser back to go to a previous tab (tab 1) & check URL syncs

      window.history.back();
      await jest.runAllTimersAsync();
      expect(window.location.toString()).toEqual(
        'http://localhost/#tab-panel-1',
      );
      expect(window.history.state).toEqual({
        'w-tabs-panel-id': 'tab-panel-1',
      });

      // check DOM state is correct
      expect(tab1.getAttribute('aria-selected')).toBe('true');
      expect(tab1Panel.hidden).toBeFalsy(); // visible
      expect(tab2Panel.hidden).toBeTruthy();
      expect(tab3Panel.hidden).toBeTruthy();

      // ensure tabindex is set correctly

      expect([tab1, tab2, tab3].map((_) => _.getAttribute('tabindex'))).toEqual(
        ['0', '-1', '-1'],
      );
    });

    it('should use the current URL hash on load to override any default tab selection', async () => {
      window.location.hash = '#tab-panel-3';

      expect(window.location.toString()).toEqual(
        'http://localhost/#tab-panel-3',
      );

      // set a conflicting DOM defaults, to ensure that the URL is used as the priority
      await setup(`
        <div id="location-tabs" data-controller="w-tabs" data-action="popstate@window->w-tabs#select" data-w-tabs-active-panel-id-value="tab-panel-4" data-w-tabs-use-location-value="true">
          <div role="tablist">
            <a id="tab-1" href="#tab-panel-1" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent">A</a>
            <a id="tab-2" href="#tab-panel-2" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent" aria-selected="true">B</a>
            <a id="tab-3" href="#tab-panel-3" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent">C</a>
            <a id="tab-4" href="#tab-panel-4" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent">D</a>
          </div>
          <section id="tab-panel-1" role="tabpanel" aria-labelledby="tab-1" data-w-tabs-target="panel">A (content)</section>
          <section id="tab-panel-2" role="tabpanel" aria-labelledby="tab-2" data-w-tabs-target="panel">B (content)</section>
          <section id="tab-panel-3" role="tabpanel" aria-labelledby="tab-3" data-w-tabs-target="panel">C (content)</section>
          <section id="tab-panel-4" role="tabpanel" aria-labelledby="tab-4" data-w-tabs-target="panel">D (content)</section>
        </div>
      `);
      expect(errors).toHaveLength(0);

      const [tab1, tab2, tab3, tab4] =
        document.querySelectorAll('[role="tab"]');
      const [tab1Panel, tab2Panel, tab3Panel, tab4Panel] =
        document.querySelectorAll('section');

      // tab-3 should be selected (from URL), not tab-2 (from aria-selected) or tab-1 (from value)

      expect(tab1.getAttribute('aria-selected')).toBe(null);
      expect(tab2.getAttribute('aria-selected')).toBe(null);
      expect(tab3.getAttribute('aria-selected')).toEqual('true');
      expect(tab4.getAttribute('aria-selected')).toBe(null);
      expect(tab1Panel.hidden).toBeTruthy();
      expect(tab2Panel.hidden).toBeTruthy();
      expect(tab3Panel.hidden).toBeFalsy();
      expect(tab4Panel.hidden).toBeTruthy();
    });

    it('should use the current URL hash on load and support any inner element', async () => {
      window.location.hash = '#inner-element';

      await setup(`
        <div id="location-tabs" data-controller="w-tabs" data-action="popstate@window->w-tabs#select" data-w-tabs-use-location-value="true">
          <div role="tablist">
            <a id="tab-1" href="#tab-panel-1" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent">A</a>
            <a id="tab-2" href="#tab-panel-2" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent">B</a>
            <a id="tab-3" href="#tab-panel-3" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent">C</a>
          </div>
          <section id="tab-panel-1" role="tabpanel" aria-labelledby="tab-1" data-w-tabs-target="panel">A (content)</section>
          <section id="tab-panel-2" role="tabpanel" aria-labelledby="tab-2" data-w-tabs-target="panel">
            B (content)
            <button type="button" id="inner-element">It's inside<button>
          </section>
          <section id="tab-panel-3" role="tabpanel" aria-labelledby="tab-3" data-w-tabs-target="panel">C (content)</section>
        </div>
      `);

      expect(errors).toHaveLength(0);

      const [tab1, tab2, tab3] = document.querySelectorAll('[role="tab"]');
      const [tab1Panel, tab2Panel, tab3Panel] =
        document.querySelectorAll('section');

      // tab-2 should be selected (from URL) because the inner element is inside the tab-panel

      expect(tab1.getAttribute('aria-selected')).toBe(null);
      expect(tab2.getAttribute('aria-selected')).toBe('true');
      expect(tab3.getAttribute('aria-selected')).toBe(null);

      expect(tab1Panel.hidden).toBeTruthy();
      expect(tab2Panel.hidden).toBeFalsy();
      expect(tab3Panel.hidden).toBeTruthy();
    });

    it('should use the current URL hash on load and support the contentpath to find the active panel', async () => {
      window.location.hash = '#:w:contentpath=abc1.d2e';

      await setup(`
        <div id="location-tabs" data-controller="w-tabs" data-action="popstate@window->w-tabs#select" data-w-tabs-use-location-value="true">
          <div role="tablist">
            <a id="tab-1" href="#tab-panel-1" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent">A</a>
            <a id="tab-2" href="#tab-panel-2" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent">B</a>
            <a id="tab-3" href="#tab-panel-3" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent">C</a>
          </div>
          <section id="tab-panel-1" role="tabpanel" aria-labelledby="tab-1" data-w-tabs-target="panel">A (content)</section>
          <section id="tab-panel-2" role="tabpanel" aria-labelledby="tab-2" data-w-tabs-target="panel">
            B (content)
            <div data-contentpath="abc1"><div data-contentpath="xyt">NOT HERE</div></div>
          </section>
          <section id="tab-panel-3" role="tabpanel" aria-labelledby="tab-3" data-w-tabs-target="panel">
            C (content)
            <div data-contentpath="abc1"><div data-contentpath="d2e">HERE</div></div>
          </section>
        </div>
      `);

      expect(errors).toHaveLength(0);

      const [tab1, tab2, tab3] = document.querySelectorAll('[role="tab"]');
      const [tab1Panel, tab2Panel, tab3Panel] =
        document.querySelectorAll('section');

      // tab-3 should be selected (from URL) because the inner element is the one in the content path

      expect(tab1.getAttribute('aria-selected')).toBe(null);
      expect(tab2.getAttribute('aria-selected')).toBe(null);
      expect(tab3.getAttribute('aria-selected')).toBe('true');

      expect(tab1Panel.hidden).toBeTruthy();
      expect(tab2Panel.hidden).toBeTruthy();
      expect(tab3Panel.hidden).toBeFalsy();
    });

    it('should use the current URL hash on load but gracefully handle not found ids', async () => {
      window.location.hash = '#goes-nowhere-does-nothing';

      await setup(`
        <div id="location-tabs" data-controller="w-tabs" data-action="popstate@window->w-tabs#select" data-w-tabs-use-location-value="true">
          <div role="tablist">
            <a id="tab-1" href="#tab-panel-1" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent">A</a>
            <a id="tab-2" href="#tab-panel-2" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent">B</a>
          </div>
          <section id="tab-panel-1" role="tabpanel" aria-labelledby="tab-1" data-w-tabs-target="panel">A (content)</section>
          <section id="tab-panel-2" role="tabpanel" aria-labelledby="tab-2" data-w-tabs-target="panel">B (content)</section>
        </div>
      `);

      expect(errors).toHaveLength(0);

      const [tab1, tab2] = document.querySelectorAll('[role="tab"]');
      const [tab1Panel, tab2Panel] = document.querySelectorAll('section');

      // should default to the first tab as the hash found an element that's not in a panel

      expect(tab1.getAttribute('aria-selected')).toBe('true');
      expect(tab2.getAttribute('aria-selected')).toBe(null);

      expect(tab1Panel.hidden).toBeFalsy();
      expect(tab2Panel.hidden).toBeTruthy();
    });

    it('should use the current URL hash on load but gracefully handle non-relevant ids', async () => {
      window.location.hash = '#not-in-a-panel';

      await setup(`
        <div id="location-tabs" data-controller="w-tabs" data-action="popstate@window->w-tabs#select" data-w-tabs-use-location-value="true">
          <div role="tablist">
            <a id="tab-1" href="#tab-panel-1" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent">A</a>
            <a id="tab-2" href="#tab-panel-2" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent">B</a>
          </div>
          <section id="tab-panel-1" role="tabpanel" aria-labelledby="tab-1" data-w-tabs-target="panel">A (content)</section>
          <section id="tab-panel-2" role="tabpanel" aria-labelledby="tab-2" data-w-tabs-target="panel">B (content)</section>
          <div id="not-in-a-panel">Not in a panel</div>
        </div>
      `);

      expect(errors).toHaveLength(0);

      const [tab1, tab2] = document.querySelectorAll('[role="tab"]');
      const [tab1Panel, tab2Panel] = document.querySelectorAll('section');

      // should default to the first tab as the hash cannot be found

      expect(tab1.getAttribute('aria-selected')).toBe('true');
      expect(tab2.getAttribute('aria-selected')).toBe(null);

      expect(tab1Panel.hidden).toBeFalsy();
      expect(tab2Panel.hidden).toBeTruthy();
    });
  });

  describe('validating tabs targets & attributes', () => {
    it('warns about role="tablist" aria attributes', async () => {
      await setup(`
      <div class="w-tabs" data-controller="w-tabs">
        <div role="not-tablist">
          <a id="tab-1" href="#tab-panel-1" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent">
            Cheese
          </a>
          <a id="tab-2" href="#tab-panel-2" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent">
            Chocolate
          </a>
          <a id="tab-3" href="#tab-panel-3" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent">
            Coffee
          </a>
        </div>
        <div class="tab-content tab-content--comments-enabled">
          <section id="tab-panel-1" class="w-tabs__panel" role="tabpanel" aria-labelledby="tab-1" data-w-tabs-target="panel">
            All about cheese
          </section>
          <section id="tab-panel-2" class="w-tabs__panel" role="tabpanel" aria-labelledby="tab-2" data-w-tabs-target="panel">
            All about chocolate
          </section>
          <section id="tab-panel-3" class="w-tabs__panel" role="tabpanel" aria-labelledby="tab-3" data-w-tabs-target="panel">
            All about coffee
          </section>
        </div>
      </div>
      `);

      expect(errors).toHaveProperty(
        '0.error.message',
        "There must be an element with `role='tablist'` within the controller's scope.",
      );
    });

    it('should warn about missing role="tab" attributes on tab triggers', async () => {
      await setup(`
      <div class="w-tabs" data-controller="w-tabs">
        <div role="tablist">
          <a id="tab-1" href="#tab-panel-1" data-action="w-tabs#select:prevent" data-w-tabs-target="trigger" role="tab">
            Cheese
          </a>
          <a id="tab-2" href="#tab-panel-2" data-action="w-tabs#select:prevent" data-w-tabs-target="trigger">
            Chocolate
          </a>
        </div>
        <div class="tab-content">
          <section id="tab-panel-1" class="w-tabs__panel" role="tabpanel" aria-labelledby="tab-1" data-w-tabs-target="panel">
            All about cheese
          </section>
          <section id="tab-panel-2" class="w-tabs__panel" role="tabpanel" aria-labelledby="tab-2" data-w-tabs-target="panel">
            All about chocolate
          </section>
        </div>
      </div>
      `);

      expect(errors).toHaveProperty(
        '0.error.message',
        'Tabs must use `role=tab`.',
      );
    });

    it('should warn about missing role="tabpanel" attributes on panel targets', async () => {
      await setup(`
      <div class="w-tabs" data-controller="w-tabs">
        <div role="tablist">
          <a id="tab-1" href="#tab-panel-1" role="tab" data-action="w-tabs#select:prevent" data-w-tabs-target="trigger">
            Cheese
          </a>
          <a id="tab-2" href="#tab-panel-2" role="tab" data-action="w-tabs#select:prevent" data-w-tabs-target="trigger">
            Chocolate
          </a>
        </div>
        <div class="tab-content">
          <section id="tab-panel-1" aria-labelledby="tab-1" data-w-tabs-target="panel">
            All about cheese
          </section>
          <section id="tab-panel-2" role="tabpanel" aria-labelledby="tab-2" data-w-tabs-target="panel">
            All about chocolate
          </section>
        </div>
      </div>
      `);

      expect(errors).toHaveProperty(
        '0.error.message',
        "Tab panel elements must have the `role='tabpanel'` attribute set",
      );
    });

    it('should warn if tab panels do not have valid aria-labelledby references to a tab', async () => {
      await setup(`
      <div class="w-tabs" data-controller="w-tabs">
        <div role="tablist">
          <a id="tab-1" href="#tab-panel-1" role="tab" data-action="w-tabs#select:prevent" data-w-tabs-target="trigger">
            Cheese
          </a>
          <a id="tab-2" href="#tab-panel-2" role="tab" data-action="w-tabs#select:prevent" data-w-tabs-target="trigger">
            Chocolate
          </a>
          <a id="tab-3" href="#tab-panel-3" role="tab" data-action="w-tabs#select:prevent" data-w-tabs-target="trigger">
            Coffee
          </a>
        </div>
        <div class="tab-content">
          <section id="tab-panel-1" role="tabpanel" aria-labelledby="tab-1" data-w-tabs-target="panel">
            All about cheese
          </section>
          <section id="tab-panel-2" role="tabpanel" aria-labelledby="tab-2" data-w-tabs-target="panel">
            All about chocolate
          </section>
          <section id="tab-panel-3" role="tabpanel" data-w-tabs-target="panel">
            All about coffee
          </section>
        </div>
      </div>
      `);

      expect(errors).toHaveProperty(
        '0.error.message',
        'Panel targets must have a panels must be labelled by their tab.',
      );
    });

    it('should warn if a tab trigger cannot be mapped to a panel to control', async () => {
      await setup(`
        <div data-controller="w-tabs">
          <div role="tablist">
            <a id="tab-1" href="#tab-panel-1" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent">A</a>
            <a id="tab-2" href="#tab-panel-2" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent">B</a>
            <a id="tab-3" href="#tab-panel-3" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent">C</a>
          </div>
          <section id="tab-panel-1" role="tabpanel" aria-labelledby="tab-1" data-w-tabs-target="panel">A (content)</section>
          <section id="tab-panel-2" role="tabpanel" aria-labelledby="tab-2" data-w-tabs-target="panel">B (content)</section>
          <!-- missing panel -->
        </div>
      `);

      expect(errors).toHaveProperty(
        '0.error.message',
        "Cannot find matching a matching panel for the trigger/tab in 'aria-controls', 'href' or 'data-w-tabs-id-param'.",
      );
    });

    it('should warn if there are no suitable tabs found', async () => {
      await setup(`
        <div data-controller="w-tabs">
          <div role="tablist"></div>
          <!-- tabs not within role='tablist' -->
          <a id="tab-1" href="#tab-panel-1" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent">A</a>
          <a id="tab-2" href="#tab-panel-2" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent">B</a>
          <a id="tab-3" href="#tab-panel-3" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent">C</a>
          <section id="tab-panel-1" role="tabpanel" aria-labelledby="tab-1" data-w-tabs-target="panel">A (content)</section>
          <section id="tab-panel-2" role="tabpanel" aria-labelledby="tab-2" data-w-tabs-target="panel">B (content)</section>
          <section id="tab-panel-3" role="tabpanel" aria-labelledby="tab-3" data-w-tabs-target="panel">C (content)</section>
        </div>
      `);

      expect(errors).toHaveProperty(
        '0.error.message',
        'Tabs must be supplied with at least one valid tab target using \'data-w-tabs-target="trigger"\' within role="tablist".',
      );
    });

    it('should warn if there are not enough tabs for the panels', async () => {
      await setup(`
        <div data-controller="w-tabs">
          <div role="tablist">
            <a id="tab-1" href="#tab-panel-1" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent">A</a>
            <a id="tab-2" href="#tab-panel-2" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent">B</a>
            <!-- incorrect target -->
            <a id="tab-3" href="#tab-panel-3" role="tab" data-w-tabs-target="missing-trigger" data-action="w-tabs#select:prevent">C</a>
          </div>
          <section id="tab-panel-1" role="tabpanel" aria-labelledby="tab-1" data-w-tabs-target="panel">A (content)</section>
          <section id="tab-panel-2" role="tabpanel" aria-labelledby="tab-2" data-w-tabs-target="panel">B (content)</section>
          <section id="tab-panel-3" role="tabpanel" aria-labelledby="tab-3" data-w-tabs-target="panel">C (content)</section>
        </div>
      `);

      expect(errors).toHaveProperty(
        '0.error.message',
        'Each tab panel must have a valid tab within the "role=tablist".',
      );
    });

    it('should warn if there are no actual panel targets', async () => {
      await setup(`
        <div data-controller="w-tabs">
          <div role="tablist">
            <a id="tab-1" href="#tab-panel-1" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent">A</a>
            <a id="tab-2" href="#tab-panel-2" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent">B</a>
            <a id="tab-3" href="#tab-panel-3" role="tab" data-w-tabs-target="trigger" data-action="w-tabs#select:prevent">C</a>
          </div>
          <section id="tab-panel-1" role="tabpanel" aria-labelledby="tab-1" data-w-tabs-target="panel-mistake">A (content)</section>
          <section id="tab-panel-2" role="tabpanel" aria-labelledby="tab-2" data-w-tabs-target="panel-typo">B (content)</section>
          <section id="tab-panel-3" role="tabpanel" aria-labelledby="tab-3">C (content)</section>
        </div>
      `);

      expect(errors).toHaveProperty(
        '0.error.message',
        `Tabs must be supplied with at least one panel target using 'data-w-tabs-target="panel"'.`,
      );
    });
  });
});
