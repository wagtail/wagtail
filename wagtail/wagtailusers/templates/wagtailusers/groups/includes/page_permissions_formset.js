$(function() {
    var panel = InlinePanel({
        formsetPrefix: "id_{{ formset.prefix }}",
        emptyChildFormPrefix: "{{ formset.empty_form.prefix }}"
    });

    {% for form in formset.forms %}
        panel.initChildControls('{{ formset.prefix }}-{{ forloop.counter0 }}');
    {% endfor %}

    panel.updateMoveButtonDisabledStates();
});
