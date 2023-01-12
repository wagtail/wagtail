import $ from 'jquery';

import { InlinePanel } from '../InlinePanel';

export class MultipleChooserPanel extends InlinePanel {
  constructor(opts) {
    super(opts);

    this.chooserWidgetFactory = window.telepath.unpack(
      JSON.parse(
        document.getElementById(`${opts.formsetPrefix}-CHOOSER_WIDGET`)
          .textContent,
      ),
    );

    $(`#${opts.formsetPrefix}-OPEN_MODAL`).on('click', () => {
      this.chooserWidgetFactory.openModal(
        (result) => {
          // eslint-disable-next-line no-console
          console.log(result);
        },
        { multiple: true },
      );
    });
  }
}
