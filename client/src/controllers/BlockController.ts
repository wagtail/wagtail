import { Controller } from '@hotwired/stimulus';

declare global {
  interface Window {
    initBlockWidget?: (id: string) => void;
    telepath: any;
  }
}

/**
 * Adds the ability to unpack a Telepath object and render it on the controlled element.
 * Used to initialize the top-level element of a BlockWidget (the form widget for a StreamField).
 *
 * @example
 * <div
 *  id="some-id"
 *  data-controller="w-block"
 *  data-w-block-data-value='{"_args":["..."], "_type": "wagtail.blocks.StreamBlock"}'
 * >
 * </div>
 *
 * @example - with initial arguments
 * <div
 *  id="some-id"
 *  data-controller="w-block"
 *  data-w-block-data-value='{"_args":["..."], "_type": "wagtail.blocks.StreamBlock"}'
 *  data-w-block-arguments-value='[[{ type: "paragraph_block", value: "..."}], {messages:["An error..."]}]'
 * >
 * </div>
 */
export class BlockController extends Controller<HTMLElement> {
  static values = {
    arguments: { type: Array, default: [] },
    data: { type: Object, default: {} },
  };

  /** Array of arguments to pass to the render method of the block [initial value, errors]. */
  declare argumentsValue: Array<string>;
  /** Block definition to be passed to `telepath.unpack`, used to obtain a JavaScript representation of the block. */
  declare dataValue: object;

  connect() {
    const telepath = window.telepath;

    if (!telepath) {
      throw new Error('`window.telepath` is not available.');
    }

    const element = this.element;
    const id = element.id;

    if (!id) {
      throw new Error('Controlled element needs an id attribute.');
    }

    const output = telepath.unpack(this.dataValue);
    output.render(element, id, ...this.argumentsValue);
    this.dispatch('ready', { detail: { ...output }, cancelable: false });
  }

  static afterLoad() {
    /**
     * Provide a backwards compatible version of the original window global function.
     *
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
