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

    const openModalButton = document.getElementById(
      `${opts.formsetPrefix}-OPEN_MODAL`,
    );
    openModalButton.addEventListener('click', () => {
      if (this.isFirstChildEmpty()) {
        openModalButton.setAttribute(
          'maxforms-remainder',
          opts.maxForms + 1 - this.getChildCount(),
        );
        openModalButton.setAttribute('maxforms', opts.maxForms);
      } else {
        openModalButton.setAttribute(
          'maxforms-remainder',
          opts.maxForms - this.getChildCount(),
        );
        openModalButton.setAttribute('maxforms', opts.maxForms);
      }

      if (Number(openModalButton.getAttribute('maxforms-remainder')) === 0) {
        openModalButton.setAttribute('disabled', 'true');
      }

      this.chooserWidgetFactory.openModal(
        (result) => {
          result.forEach((item) => {
            if (this.isFirstChildEmpty()) {
              if (opts.maxForms && this.getChildCount() >= opts.maxForms + 1)
                return;
            } else if (opts.maxForms && this.getChildCount() >= opts.maxForms)
              return;
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

  updateOpenModalButtonState() {
    if (this.opts.maxForms) {
      const openModalButton = document.getElementById(
        `${this.opts.formsetPrefix}-OPEN_MODAL`,
      );
      const firstChildButton = this.getFirstchild()
        .querySelector('.unchosen')
        .querySelector('button');
      if (this.isFirstChildEmpty()) {
        firstChildButton.setAttribute(
          'maxforms-remainder',
          this.opts.maxForms + 1 - this.getChildCount(),
        );
      }
      if (
        this.isFirstChildEmpty()
          ? this.getChildCount() >= this.opts.maxForms + 1
          : this.getChildCount() >= this.opts.maxForms
      ) {
        // need to set the data-force-disabled attribute to override the standard modal-workflow
        // behaviour of re-enabling the button after the modal closes (which potentially happens
        // after this code has run)
        openModalButton.setAttribute('disabled', 'true');
        openModalButton.setAttribute('data-force-disabled', 'true');
        if (firstChildButton) firstChildButton.setAttribute('disabled', 'true');
      } else {
        openModalButton.removeAttribute('disabled');
        openModalButton.removeAttribute('data-force-disabled');
        if (firstChildButton) firstChildButton.removeAttribute('disabled');
      }
    }
  }

  updateControlStates() {
    super.updateControlStates();
    this.updateOpenModalButtonState();
  }
}
