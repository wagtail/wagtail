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
          result.forEach((item) => {
            this.addForm();
            const formIndex = this.formCount - 1;
            const formPrefix = `${opts.formsetPrefix}-${formIndex}`;
            const chooserFieldId = `${formPrefix}-${opts.chooserFieldName}`;
            const chooserWidget =
              this.chooserWidgetFactory.getById(chooserFieldId);
            chooserWidget.setStateFromModalData(item);
          });
        },
        { multiple: true },
      );
    });
  }
}
