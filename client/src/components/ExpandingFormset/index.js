import $ from 'jquery';

/**
 * Usage of this class directly is deprecated for admin core code use.
 * Class still needs to be in place for legacy support (see `window.buildExpandingFormset`)
 * and it's being extended by InlinePanel & MultipleChooserPanel.
 *
 * @deprecated - Will be removed in a future release once fully migrated to Stimulus.
 * @see `client/src/controllers/FormsetController.ts` for the future (WIP) implementation.
 */
export class ExpandingFormset {
  constructor(prefix, opts = {}) {
    this.opts = opts;
    const addButton = $('#' + prefix + '-ADD');
    this.formContainer = $('#' + prefix + '-FORMS');
    this.totalFormsInput = $('#' + prefix + '-TOTAL_FORMS');
    this.formCount = parseInt(this.totalFormsInput.val(), 10);

    if (opts.onInit) {
      for (let i = 0; i < this.formCount; i += 1) {
        opts.onInit(i);
      }
    }

    const emptyFormElement = document.getElementById(
      prefix + '-EMPTY_FORM_TEMPLATE',
    );

    this.emptyFormTemplate = emptyFormElement.innerHTML;

    addButton.on('click', () => {
      this.addForm();
    });
  }

  /**
   * @param {object?} opts
   * @param {boolean?} opts.runCallbacks - (default: true) - if false, the onAdd and onInit callbacks will not be run
   */
  addForm(opts = {}) {
    const formIndex = this.formCount;
    const newFormHtml = this.emptyFormTemplate.replace(
      /__prefix__(.*?['"])/g,
      formIndex + '$1',
    );

    this.formContainer.append(newFormHtml);

    this.formCount += 1;
    this.totalFormsInput.val(this.formCount);

    if (!('runCallbacks' in opts) || opts.runCallbacks) {
      if (this.opts.onAdd) this.opts.onAdd(formIndex);
      if (this.opts.onInit) this.opts.onInit(formIndex);
    }
  }
}
