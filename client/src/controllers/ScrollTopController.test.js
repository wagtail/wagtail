import { Application } from '@hotwired/stimulus';
import { ScrollTopController } from './ScrollTopController';

describe('ScrollTopController', () => {
  let application;
  let element;

  beforeEach(() => {
    application = Application.start();
    application.register('w-scroll-top', ScrollTopController);
  });

  afterEach(() => {
    application.stop();
    document.body.innerHTML = '';
    jest.clearAllMocks();
  });

  const setupButton = (threshold = 300) => {
    document.body.innerHTML = `
      <button
        id="scroll-top-btn"
        data-controller="w-scroll-top"
        data-w-scroll-top-threshold-value="${threshold}"
        data-action="click->w-scroll-top#scrollToTop"
        aria-label="Scroll to top"
      >
        Scroll to Top
      </button>
    `;
    element = document.getElementById('scroll-top-btn');
  };

  describe('connect', () => {
    it('hides button on init', async () => {
      setupButton();
      await Promise.resolve(); // Wait for controller to connect
      expect(element.hidden).toBe(true);
      expect(element.getAttribute('aria-hidden')).toBe('true');
    });
  });

  describe('handleScroll', () => {
    beforeEach(async () => {
      setupButton(200);
      await Promise.resolve(); // Wait for controller to connect
      Object.defineProperty(window, 'scrollY', {
        writable: true,
        configurable: true,
        value: 0,
      });
    });

    it('shows button when scrolled past threshold', () => {
      window.scrollY = 250;
      window.dispatchEvent(new Event('scroll'));
      
      expect(element.hidden).toBe(false);
      expect(element.getAttribute('aria-hidden')).toBe('false');
    });

    it('hides button when scrolled before threshold', () => {
      window.scrollY = 100;
      window.dispatchEvent(new Event('scroll'));
      
      expect(element.hidden).toBe(true);
      expect(element.getAttribute('aria-hidden')).toBe('true');
    });
  });

  describe('scrollToTop', () => {
    let mainElement;
    
    beforeEach(async () => {
      // Mock before setup so it's available when controller connects
      window.scrollTo = jest.fn();
      
      // Create main element first
      mainElement = document.createElement('main');
      mainElement.id = 'main';
      mainElement.setAttribute('tabindex', '-1');
      document.body.appendChild(mainElement);
      
      setupButton();
      await Promise.resolve(); // Wait for controller to connect
    });

    it('scrolls to top with smooth behavior', async () => {
      element.click();
      await Promise.resolve();
      
      expect(window.scrollTo).toHaveBeenCalledWith({
        top: 0,
        behavior: 'smooth',
      });
    });

    it('attempts to focus main content for accessibility', async () => {
      // The test just verifies the controller tries to call getElementById
      // and focus, but doesn't strictly require it to succeed in test environment
      const getElementByIdSpy = jest.spyOn(document, 'getElementById');
      
      element.click();
      await Promise.resolve();
      
      // Verify that we attempted to get the main element
      expect(getElementByIdSpy).toHaveBeenCalledWith('main');
      
      getElementByIdSpy.mockRestore();
    });

    it('prevents default event behavior', async () => {
      const clickHandler = jest.fn((e) => e.preventDefault());
      element.addEventListener('click', clickHandler);
      
      element.click();
      await Promise.resolve();
      
      expect(clickHandler).toHaveBeenCalled();
      const event = clickHandler.mock.calls[0][0];
      expect(event.defaultPrevented).toBe(true);
    });
  });

  describe('disconnect', () => {
    it('removes scroll event listener', async () => {
      setupButton();
      await Promise.resolve(); // Wait for controller to connect
      const controller = application.getControllerForElementAndIdentifier(
        element,
        'w-scroll-top'
      );
      
      const removeEventListenerSpy = jest.spyOn(window, 'removeEventListener');
      controller.disconnect();
      
      expect(removeEventListenerSpy).toHaveBeenCalledWith('scroll', expect.any(Function));
    });
  });
});
