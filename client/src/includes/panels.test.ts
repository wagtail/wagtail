import {
  initAnchoredPanels,
  initCollapsiblePanel,
  initCollapsiblePanels,
  toggleCollapsiblePanel,
} from './panels';

describe('panels', () => {
  let toggle: HTMLButtonElement;
  let content: HTMLDivElement;
  let panel: HTMLDivElement;
  let heading: HTMLDivElement;

  beforeEach(() => {
    jest.restoreAllMocks();
    localStorage.clear();
    document.body.innerHTML = `
      <div data-panel class="collapsed">
        <div data-panel-heading>Panel Heading</div>
        <button id="toggle-1" data-panel-toggle aria-expanded="true" aria-controls="content-1"></button>
        <div id="content-1">
           Panel Content
        </div>
      </div>
    `;
    panel = document.querySelector('[data-panel]') as HTMLDivElement;
    heading = document.querySelector('[data-panel-heading]') as HTMLDivElement;
    toggle = document.querySelector('[data-panel-toggle]') as HTMLButtonElement;
    content = document.querySelector('#content-1') as HTMLDivElement;
  });

  describe('toggleCollapsiblePanel', () => {
    it('collapses panel and saves to localStorage', () => {
      // By default, toggles expanded state (which is true initially) -> collapses it
      toggleCollapsiblePanel(toggle);
      expect(toggle.getAttribute('aria-expanded')).toBe('false');
      expect(content.hasAttribute('hidden')).toBe(true);
      expect(localStorage.getItem('wagtail:collapsed-panel:content-1')).toBe(
        'true',
      );

      // Now toggle again to expand
      toggleCollapsiblePanel(toggle);
      expect(toggle.getAttribute('aria-expanded')).toBe('true');
      expect(content.hasAttribute('hidden')).toBe(false);
      expect(localStorage.getItem('wagtail:collapsed-panel:content-1')).toBe(
        'false',
      );
    });

    it('uses until-found when supported by browser', () => {
      // Mock 'onbeforematch' in document.body to simulate browser support
      Object.defineProperty(document.body, 'onbeforematch', {
        value: null,
        writable: true,
        configurable: true,
      });

      toggleCollapsiblePanel(toggle, false); // force collapse
      expect(content.getAttribute('hidden')).toBe('until-found');

      delete (document.body as any).onbeforematch;
    });

    it('dispatches custom events', () => {
      const commentAnchorSpy = jest.fn();
      const panelToggleSpy = jest.fn();

      toggle.addEventListener(
        'commentAnchorVisibilityChange',
        commentAnchorSpy,
      );
      toggle.addEventListener('wagtail:panel-toggle', panelToggleSpy);

      toggleCollapsiblePanel(toggle, true);

      expect(commentAnchorSpy).toHaveBeenCalled();
      expect(panelToggleSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          detail: { expanded: true },
        }),
      );
    });

    it('handles localStorage errors gracefully', () => {
      const spy = jest
        .spyOn(Storage.prototype, 'setItem')
        .mockImplementation(() => {
          throw new Error('Storage full');
        });

      // Should not throw
      expect(() => toggleCollapsiblePanel(toggle, true)).not.toThrow();
      expect(toggle.getAttribute('aria-expanded')).toBe('true');
      spy.mockRestore();
    });
  });

  describe('initCollapsiblePanel', () => {
    it('sets initial collapsed state from class list if no localStorage exists', () => {
      initCollapsiblePanel(toggle);
      expect(toggle.getAttribute('aria-expanded')).toBe('false');
      expect(content.hasAttribute('hidden')).toBe(true);
    });

    it('sets initial expanded state from class list if not marked collapsed', () => {
      panel.classList.remove('collapsed');
      initCollapsiblePanel(toggle);
      expect(toggle.getAttribute('aria-expanded')).toBe('true');
      expect(content.hasAttribute('hidden')).toBe(false);
    });

    it('respects localStorage expanded state', () => {
      localStorage.setItem('wagtail:collapsed-panel:content-1', 'false');
      initCollapsiblePanel(toggle);
      expect(toggle.getAttribute('aria-expanded')).toBe('true');
      expect(content.hasAttribute('hidden')).toBe(false);
    });

    it('respects localStorage collapsed state', () => {
      panel.classList.remove('collapsed');
      localStorage.setItem('wagtail:collapsed-panel:content-1', 'true');
      initCollapsiblePanel(toggle);
      expect(toggle.getAttribute('aria-expanded')).toBe('false');
      expect(content.hasAttribute('hidden')).toBe(true);
    });

    it('does not collapse if panel has validation error', () => {
      content.innerHTML = '<span class="error">Field is required</span>';
      localStorage.setItem('wagtail:collapsed-panel:content-1', 'true');
      initCollapsiblePanel(toggle);
      expect(toggle.getAttribute('aria-expanded')).toBe('true');
      expect(content.hasAttribute('hidden')).toBe(false);
    });

    it('sets click event listeners on toggle and heading', () => {
      initCollapsiblePanel(toggle);

      // Initial state is collapsed (aria-expanded = false) because data-panel has class "collapsed"
      expect(toggle.getAttribute('aria-expanded')).toBe('false');

      // Click toggle
      toggle.click();
      expect(toggle.getAttribute('aria-expanded')).toBe('true');

      // Click heading
      heading.click();
      expect(toggle.getAttribute('aria-expanded')).toBe('false');
    });

    it('listens for beforematch event on content to expand panel', () => {
      initCollapsiblePanel(toggle);
      expect(toggle.getAttribute('aria-expanded')).toBe('false');

      content.dispatchEvent(new CustomEvent('beforematch'));
      expect(toggle.getAttribute('aria-expanded')).toBe('true');
    });

    it('dispatches wagtail:panel-init event', () => {
      const initSpy = jest.fn();
      toggle.addEventListener('wagtail:panel-init', initSpy);

      initCollapsiblePanel(toggle);
      expect(initSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          detail: { expanded: false },
        }),
      );
    });

    it('avoids initializing the same panel twice', () => {
      initCollapsiblePanel(toggle);

      expect((panel as any).collapsibleInitialised).toBe(true);

      // Modifying aria-controls to a non-existent element should do nothing because it returns early.
      toggle.setAttribute('aria-controls', 'non-existent');
      expect(() => initCollapsiblePanel(toggle)).not.toThrow();
    });

    it('handles localStorage.getItem exceptions gracefully', () => {
      const spy = jest
        .spyOn(Storage.prototype, 'getItem')
        .mockImplementation(() => {
          throw new Error('Blocked storage');
        });

      expect(() => initCollapsiblePanel(toggle)).not.toThrow();
      expect(toggle.getAttribute('aria-expanded')).toBe('false'); // defaults to class-based collapsed
      spy.mockRestore();
    });
  });

  describe('initCollapsiblePanels', () => {
    it('initializes multiple panels', () => {
      document.body.innerHTML = `
        <div data-panel class="collapsed">
          <button id="toggle-1" data-panel-toggle aria-expanded="true" aria-controls="content-1"></button>
          <div id="content-1"></div>
        </div>
        <div data-panel class="collapsed">
          <button id="toggle-2" data-panel-toggle aria-expanded="true" aria-controls="content-2"></button>
          <div id="content-2"></div>
        </div>
      `;
      initCollapsiblePanels();

      const toggle1 = document.getElementById('toggle-1') as HTMLButtonElement;
      const toggle2 = document.getElementById('toggle-2') as HTMLButtonElement;

      expect(
        (toggle1.closest('[data-panel]') as any).collapsibleInitialised,
      ).toBe(true);
      expect(
        (toggle2.closest('[data-panel]') as any).collapsibleInitialised,
      ).toBe(true);
    });
  });

  describe('initAnchoredPanels', () => {
    beforeEach(() => {
      jest.useFakeTimers();
    });

    afterEach(() => {
      jest.useRealTimers();
    });

    it('scrolls to element by hash or content path target', () => {
      const target = document.createElement('div');
      target.id = 'anchor-target';
      target.setAttribute('data-panel', '');
      const scrollSpy = jest.fn();
      target.scrollIntoView = scrollSpy;
      document.body.appendChild(target);

      initAnchoredPanels(target);
      jest.runAllTimers();

      expect(scrollSpy).toHaveBeenCalledWith({ behavior: 'smooth' });
    });
  });
});
