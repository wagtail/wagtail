import { Controller } from '@hotwired/stimulus';
import { object } from 'prop-types';

declare global {
  interface Window {
    initBlockWidget?: (id: string) => void; // Declare the initBlockWidget function as optional on the Window interface
    telepath: any;
  }
}

/**
 * Adds the ability to unpack a Telepath object and render it on the controlled element.
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
    initial: { type: object, default: undefined },
    data: { type: object, default: undefined },
    error: { type: object, default: undefined },
  };

  /** Packed Telepath data. */
  declare dataValue: object;
  declare errorValue: object;
  declare initialValue: object;

  connect() {
    const telepath = window.telepath;
    if (!telepath) {
      throw new Error("Telepath doesn't exit");
    }
    const output = telepath.unpack(this.dataValue);
    const element = this.element;
    if (!element.id) {
      // Throw an error here saying that the element needs an id. I think... Only of the block render code needs an id.
      throw new Error('Block element needs an id');
    }
    const id = element.id;
    output.render(this.element, id, this.initialValue, this.errorValue);
    this.dispatch('ready', { detail: { ...output }, cancelable: false });
  }

  static afterLoad() {
    /**
     * @deprecated RemovedInWagtail70
     */
    window.initBlockWidget = (id: string) => {
      const body = document.querySelector(
        '#' + id + '[data-block]',
      ) as HTMLElement;

      if (!body) {
        return;
      }

      const blockDefData = JSON.parse(body.dataset.wBlockDataValue as string);
      if (window.telepath) {
        const blockDef = window.telepath.unpack(blockDefData);
        const blockValue = JSON.parse(
          body.dataset.wBlockInitialValue as string,
        );
        const blockError = JSON.parse(body.dataset.wBlockErrorValue as string);

        blockDef.render(body, id, blockValue, blockError);
      }
    };
  }
}
