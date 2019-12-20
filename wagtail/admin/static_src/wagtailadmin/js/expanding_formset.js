function buildExpandingFormset(prefix, opts) {
    if (!opts) {
        opts = {};
    }

    var addButton = $('#' + prefix + '-ADD');
    var formContainer = $('#' + prefix + '-FORMS');
    var totalFormsInput = $('#' + prefix + '-TOTAL_FORMS');
    var formCount = parseInt(totalFormsInput.val(), 10);

    if (opts.onInit) {
        for (var i = 0; i < formCount; i++) {
            opts.onInit(i);
        }
    }

    var emptyFormTemplate = document.getElementById(prefix + '-EMPTY_FORM_TEMPLATE');
    if (emptyFormTemplate.innerText) {
        emptyFormTemplate = emptyFormTemplate.innerText;
    } else if (emptyFormTemplate.textContent) {
        emptyFormTemplate = emptyFormTemplate.textContent;
    }

    addButton.on('click', function() {
        if (addButton.hasClass('disabled')) return false;
        var newFormHtml = emptyFormTemplate
            .replace(/__prefix__/g, formCount)
            .replace(/<-(-*)\/script>/g, '<$1/script>');
        formContainer.append(newFormHtml);
        if (opts.onAdd) opts.onAdd(formCount);
        if (opts.onInit) opts.onInit(formCount);

        formCount++;
        totalFormsInput.val(formCount);
    });
}
