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
    console.log('THIS THING ON???', opts, openModalButton);

    openModalButton.addEventListener('click', () => {
      // console.log('OPEN MODAL BUTTON CLICKED', { ...opts });
      // need to get the TOTAL_FORMS, INITIAL_FORMS, and MAX_NUM_FORMS from the formset

      const maxForms = opts.maxForms;
      const totalForms = Number(
        document.getElementById(`${opts.formsetPrefix}-TOTAL_FORMS`)?.value ||
          0,
      );
      // const maxMultiple = maxForms ? maxForms - totalForms : true;

      console.log(
        'OPEN MODAL BUTTON CLICKED',
        { ...opts },
        {
          maxForms,
          totalForms,
          // maxMultiple,
        },
      );

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
            // THIS RUNS AFTER SELECTION!!@##!@
            console.log('multi-chooser-panel', {
              item,
              chooserWidget,
              opts,
              count: this.getChildCount(),
            });
            chooserWidget.setStateFromModalData(item);
          });
        },
        { available: maxForms - totalForms, multiple: maxForms },
      );
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
