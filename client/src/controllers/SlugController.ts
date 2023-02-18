import { Controller } from '@hotwired/stimulus';
import { cleanForSlug } from '../utils/text';

/**
 * Adds ability to slugify the value of an input element.
 *
 * @example
 * <input type="text" name="slug" data-controller="w-slug" data-action="blur->w-slug#slugify" />
 */
export class SlugController extends Controller<HTMLInputElement> {
  static values = {
    allowUnicode: { default: false, type: Boolean },
  };

  declare allowUnicodeValue: boolean;

  slugify() {
    this.element.value = cleanForSlug(this.element.value.trim(), false, {
      unicodeSlugsEnabled: this.allowUnicodeValue,
    });
  }
}
