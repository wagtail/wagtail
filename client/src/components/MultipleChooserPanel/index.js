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

    const getChoiceSelectIds = () => {
      const forms = this.getActiveForms();
      const choiceIds = [];

      // eslint-disable-next-line func-names
      forms.each(function () {
        const inputValId = $(this)
          .find('input[type="hidden"][choice-select-val-id]')
          .val();

        if (
          inputValId !== undefined &&
          typeof parseInt(inputValId, 10) === 'number' &&
          inputValId !== ''
        ) {
          choiceIds.push(inputValId);
        }
      });
      return choiceIds;
    };

    const openModalButton = document.getElementById(
      `${opts.formsetPrefix}-OPEN_MODAL`,
    );
    openModalButton.addEventListener('click', () => {
      this.chooserWidgetFactory.openModal(
        (result) => {
          result.forEach((item) => {
            if (opts.maxForms && this.getChildCount() >= opts.maxForms) return;
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
      if (opts.allowDuplicates === 'True') {
        openModalButton.setAttribute(
          'chooserids',
          getChoiceSelectIds().join(','),
        );
      }
    });
  }

  updateOpenModalButtonState() {
    if (this.opts.maxForms) {
      const openModalButton = document.getElementById(
        `${this.opts.formsetPrefix}-OPEN_MODAL`,
      );
      if (this.getChildCount() >= this.opts.maxForms) {
        // need to set the data-force-disabled attribute to override the standard modal-workflow
        // behaviour of re-enabling the button after the modal closes (which potentially happens
        // after this code has run)
        openModalButton.setAttribute('disabled', 'true');
        openModalButton.setAttribute('data-force-disabled', 'true');
      } else {
        openModalButton.removeAttribute('disabled');
        openModalButton.removeAttribute('data-force-disabled');
      }
    }
  }

  updateControlStates() {
    super.updateControlStates();
    this.updateOpenModalButtonState();
  }
}
