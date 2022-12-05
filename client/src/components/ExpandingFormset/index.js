import $ from 'jquery';

export class ExpandingFormset {
  constructor(prefix, opts = {}) {
    this.expandingFormsetOpts = opts;
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
    if (emptyFormElement.innerText) {
      this.emptyFormTemplate = emptyFormElement.innerText;
    } else if (emptyFormElement.textContent) {
      this.emptyFormTemplate = emptyFormElement.textContent;
    }

    addButton.on('click', () => {
      this.addForm();
    });
  }

  addForm(opts = {}) {
    /*
    Supported opts:
    runCallbacks (default: true) - if false, the onAdd and onInit callbacks will not be run
    */
    const formIndex = this.formCount;
    const newFormHtml = this.emptyFormTemplate
      .replace(/__prefix__(.*?['"])/g, formIndex + '$1')
      .replace(/<-(-*)\/script>/g, '<$1/script>');

    this.formContainer.append(newFormHtml);

    this.formCount += 1;
    this.totalFormsInput.val(this.formCount);

    if (!('runCallbacks' in opts) || opts.runCallbacks) {
      if (this.expandingFormsetOpts.onAdd)
        this.expandingFormsetOpts.onAdd(formIndex);
      if (this.expandingFormsetOpts.onInit)
        this.expandingFormsetOpts.onInit(formIndex);
    }
  }
}
