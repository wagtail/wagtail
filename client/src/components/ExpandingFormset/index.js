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
    if (emptyFormElement.innerText) {
      this.emptyFormTemplate = emptyFormElement.innerText;
    } else if (emptyFormElement.textContent) {
      this.emptyFormTemplate = emptyFormElement.textContent;
    }

    addButton.on('click', () => {
      this.addForm();
    });
  }

  addForm() {
    const newFormHtml = this.emptyFormTemplate
      .replace(/__prefix__(.*?['"])/g, this.formCount + '$1')
      .replace(/<-(-*)\/script>/g, '<$1/script>');

    this.formContainer.append(newFormHtml);
    if (this.opts.onAdd) this.opts.onAdd(this.formCount);
    if (this.opts.onInit) this.opts.onInit(this.formCount);

    this.formCount += 1;
    this.totalFormsInput.val(this.formCount);
  }
}
