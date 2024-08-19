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
      const chooserIds = [];
      const formsIndexes = this.getActiveFormsIndex();

      for (const formIndex of formsIndexes) {
        const formPrefix = `${opts.formsetPrefix}-${formIndex}`;
        const chooserFieldId = `${formPrefix}-${opts.chooserFieldName}`;
        const chooserWidget = this.chooserWidgetFactory.getById(chooserFieldId);

        if (
          chooserWidget !== null &&
          chooserWidget.state !== null &&
          chooserWidget.state.id !== null
        ) {
          chooserIds.push(chooserWidget.state.id);
        }
      }
      return chooserIds;
    };

    const openModalButton = document.getElementById(
      `${opts.formsetPrefix}-OPEN_MODAL`,
    );
    openModalButton.addEventListener('click', () => {
      const queryParams = { multiple: true };
      if (opts.allowDuplicates) {
        queryParams.chooserIds = getChoiceSelectIds().join(',');
      }
      this.chooserWidgetFactory.openModal((result) => {
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
      }, queryParams);
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
