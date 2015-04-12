$(function() {
    var prefix = '{{formset.prefix}}';
    var emptyPrefix = '{{formset.empty_form.prefix}}';
    var numForms = parseInt('{{formset.forms|length}}', 10);

    var panel = InlinePanel({
        formsetPrefix: 'id_' + prefix,
        emptyChildFormPrefix: emptyPrefix,
    });

    for (var i = 0; i < numForms; i++) {
        panel.initChildControls([prefix, i].join('-'));
    }

    panel.updateMoveButtonDisabledStates();
});
