import { Controller } from '@hotwired/stimulus';
import { object } from 'prop-types';

declare global {
  interface Window {
    initBlockWidget?: (id: string) => void; // Declare the initBlockWidget function as optional on the Window interface
    telepath?: any;
  }
}

/**
 * Adds the ability to control a block element.
 *
 * @example
 * <div
 * id="{id}"
 * data-block
 * data-controller="w-block"
 * data-w-block-data-value="{block_json}"
 * data-w-block-initial-value="{value_json}"
 * data-w-block-error-value="{error_json}">
 * </div>
 */

export class BlockController extends Controller<HTMLElement> {
  /**
   * initial - Initial value for the block
   * data - Unpacked Telepath data
   * error - Block error (optional)
   */
  static values = {
    initial: { type: object, default: {} },
    data: { type: object, default: {} },
    error: { type: object, default: {} },
  };

  /** Packed Telepath data. */
  declare dataValue: object;
  declare errorValue: object;
  declare initialValue: object;

  connect() {
    const output = window.telepath.unpack(this.dataValue);
    output.render(
      this.element,
      this.element.id,
      this.initialValue,
      this.errorValue,
    );
    this.dispatch('ready', { detail: { ...output }, cancelable: false });
  }

  static afterLoad() {
    window.initBlockWidget = (id: string) => {
      const body = document.querySelector(
        '#' + id + '[data-block]',
      ) as HTMLElement;

      if (!body) {
        return;
      }

      const blockDefData = JSON.parse(body.dataset.data as string);
      if (window.telepath) {
        const blockDef = window.telepath.unpack(blockDefData);
        const blockValue = JSON.parse(body.dataset.value as string);
        const blockError = JSON.parse(body.dataset.error as string);

        blockDef.render(body, id, blockValue, blockError);
      }
    };
  }
}
