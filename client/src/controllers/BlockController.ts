import { Controller } from '@hotwired/stimulus';

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
 *  id="some-id"
 *  data-controller="w-block"
 *  data-w-block-data-value='{"some":"json"}'
 * >
 * </div>
 */
export class BlockController extends Controller<HTMLElement> {
  static values = {
    initial: { type: Array, default: [] },
    error: { type: Object, default: {} },
    data: { type: Object, default: {} },
  };

  /** Initial value. */
  declare initialValue: Array<string>;
  /** Optional error value. */
  declare errorValue: Object;
  /** Block data value to unpack with Telepath. */
  declare dataValue: Object;

  connect() {
    const element = this.element;
    const id = element.id;

    if (!id) throw new Error('Block element needs an id');

    const telepath = window.telepath;

    if (!telepath) throw new Error("Telepath doesn't exit");

    const output = telepath.unpack(this.dataValue);
    output.render(element, id, this.initialValue, this.errorValue);

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
