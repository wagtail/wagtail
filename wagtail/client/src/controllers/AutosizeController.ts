import { Controller } from '@hotwired/stimulus';
import autosize from 'autosize';
import { debounce } from '../utils/debounce';

/**
 * Adds the ability for a text area element to be auto-sized as the user
 * types in the field so that it expands to show all content.
 *
 * @example
 * ```html
 * <textarea data-controller="w-autosize"></textarea>
 * ```
 */
export class AutosizeController extends Controller<HTMLTextAreaElement> {
  resizeObserver?: ResizeObserver;

  resize() {
    autosize.update(this.element);
  }

  initialize() {
    this.resize = debounce(this.resize.bind(this), 50);
  }

  connect() {
    autosize(this.element);
    this.resizeObserver = new ResizeObserver(this.resize);
    this.resizeObserver.observe(this.element);
  }

  disconnect() {
    this.resizeObserver?.disconnect();
    autosize.destroy(this.element);
  }
}
