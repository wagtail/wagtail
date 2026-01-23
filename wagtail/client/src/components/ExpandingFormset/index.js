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
  constructor(prefix, opts = {}, initControls = true) {
    this.opts = opts;
    const addButton = $('#' + prefix + '-ADD');
    this.formContainer = $('#' + prefix + '-FORMS');
    this.totalFormsInput = $('#' + prefix + '-TOTAL_FORMS');

    const emptyFormElement = document.getElementById(
      prefix + '-EMPTY_FORM_TEMPLATE',
    );

    this.emptyFormTemplate = emptyFormElement.innerHTML;

    if (initControls) {
      if (opts.onInit) {
        for (let i = 0; i < this.formCount; i += 1) {
          opts.onInit(i);
        }
      }

      addButton.on('click', () => {
        this.addForm();
      });
    }
  }

  get formCount() {
    return parseInt(this.totalFormsInput.val(), 10);
  }

  /**
   * @param {object?} opts
   * @param {boolean?} opts.runCallbacks - (default: true) - if false, the onAdd and onInit callbacks will not be run
   */
  addForm(opts = {}) {
    const formIndex = this.formCount;
    const newFormHtml = this.emptyFormTemplate.replace(
      /__prefix__(.*?('|"|\\u0022))/g,
      formIndex + '$1',
    );

    this.formContainer.append(newFormHtml);

    this.totalFormsInput.val(this.formCount + 1);

    if (!('runCallbacks' in opts) || opts.runCallbacks) {
      if (this.opts.onAdd) this.opts.onAdd(formIndex);
      if (this.opts.onInit) this.opts.onInit(formIndex);
    }
  }
}
