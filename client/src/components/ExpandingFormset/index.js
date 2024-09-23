import $ from 'jquery';

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

    if (emptyFormElement instanceof HTMLTemplateElement) {
      this.emptyFormTemplate = emptyFormElement.innerHTML;
    } else if (emptyFormElement instanceof HTMLScriptElement) {
      /**
       * Support legacy `<script type="text/django-form-template">` until removed
       * @deprecated RemovedInWagtail70
       */
      this.emptyFormTemplate =
        emptyFormElement.innerText || emptyFormElement.textContent;
    }

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
    const newFormHtml = this.emptyFormTemplate
      .replace(/__prefix__(.*?['"])/g, formIndex + '$1')
      /**
       * Replace inner escaped `<script>...<-/script>` tags with `<script>` tags
       * @deprecated RemovedInWagtail70
       */
      .replace(/<-(-*)\/script>/g, '<$1/script>');

    this.formContainer.append(newFormHtml);

    this.formCount += 1;
    this.totalFormsInput.val(this.formCount);

    if (!('runCallbacks' in opts) || opts.runCallbacks) {
      if (this.opts.onAdd) this.opts.onAdd(formIndex);
      if (this.opts.onInit) this.opts.onInit(formIndex);
    }
  }
}
