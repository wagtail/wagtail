import { Controller } from '@hotwired/stimulus';
import autosize from 'autosize';
import { debounce } from '../utils/debounce';

/**
 * Adds the ability for a text area field to automatically increase in
 * size as a user types into the field.
 *
 * @example
 * <textarea data-controller="w-autosize"></textarea>
 */
export class AutosizeController extends Controller<HTMLTextAreaElement> {
  resizeObserver?: ResizeObserver;

  initialize() {
    this.resize = debounce(this.resize.bind(this), 50);
  }

  connect() {
    autosize(this.element);

    this.resizeObserver = new ResizeObserver(this.resize);
    this.resizeObserver.observe(this.element);
  }

  resize() {
    autosize.update(this.element);
  }

  disconnect() {
    this.resizeObserver?.disconnect();
    autosize.destroy(this.element);
  }
}
