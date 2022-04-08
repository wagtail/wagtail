import $ from 'jquery';

function buildExpandingFormset(prefix, opts = {}) {
  const addButton = $('#' + prefix + '-ADD');
  const formContainer = $('#' + prefix + '-FORMS');
  const totalFormsInput = $('#' + prefix + '-TOTAL_FORMS');
  let formCount = parseInt(totalFormsInput.val(), 10);

  if (opts.onInit) {
    for (let i = 0; i < formCount; i++) {
      opts.onInit(i);
    }
  }

  let emptyFormTemplate = document.getElementById(
    prefix + '-EMPTY_FORM_TEMPLATE',
  );
  if (emptyFormTemplate.innerText) {
    emptyFormTemplate = emptyFormTemplate.innerText;
  } else if (emptyFormTemplate.textContent) {
    emptyFormTemplate = emptyFormTemplate.textContent;
  }

  // eslint-disable-next-line consistent-return
  addButton.on('click', () => {
    if (addButton.hasClass('disabled')) return false;
    const newFormHtml = emptyFormTemplate
      .replace(/__prefix__(.*?['"])/g, formCount + '$1')
      .replace(/<-(-*)\/script>/g, '<$1/script>');
    formContainer.append(newFormHtml);
    if (opts.onAdd) opts.onAdd(formCount);
    if (opts.onInit) opts.onInit(formCount);

    formCount++;
    totalFormsInput.val(formCount);
  });
}
window.buildExpandingFormset = buildExpandingFormset;
