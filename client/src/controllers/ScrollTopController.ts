import { Controller } from '@hotwired/stimulus';

/**
 * Adds a scroll-to-top button that appears when user scrolls down
 * and smoothly scrolls back to the top when clicked.
 *
 * @example
 * <button
 *   data-controller="w-scroll-top"
 *   data-w-scroll-top-threshold-value="300"
 *   data-action="click->w-scroll-top#scrollToTop"
 * >
 *   Scroll to Top
 * </button>
 */
export class ScrollTopController extends Controller<HTMLButtonElement> {
  static values = {
    threshold: { type: Number, default: 300 },
  };

  declare thresholdValue: number;

  connect() {
    this.handleScroll = this.handleScroll.bind(this);
    this.hide();
    window.addEventListener('scroll', this.handleScroll, { passive: true });
  }

  disconnect() {
    window.removeEventListener('scroll', this.handleScroll);
  }

  handleScroll() {
    if (window.scrollY > this.thresholdValue) {
      this.show();
    } else {
      this.hide();
    }
  }

  show() {
    this.element.hidden = false;
    this.element.setAttribute('aria-hidden', 'false');
  }

  hide() {
    this.element.hidden = true;
    this.element.setAttribute('aria-hidden', 'true');
  }

  scrollToTop(event: Event) {
    event.preventDefault();
    window.scrollTo({
      top: 0,
      behavior: 'smooth',
    });
    // Set focus to the main content for accessibility
    const main = document.getElementById('main');
    if (main) {
      main.focus({ preventScroll: true });
    }
  }
}
