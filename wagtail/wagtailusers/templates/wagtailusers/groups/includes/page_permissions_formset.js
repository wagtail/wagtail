(function() {
    function fixPrefix(str) {return str;}

    $(function() {
        var panel = InlinePanel({
            formsetPrefix: fixPrefix("id_{{ formset.prefix }}"),
            emptyChildFormPrefix: fixPrefix("{{ formset.empty_form.prefix }}")
        });

        {% for form in formset.forms %}
            panel.initChildControls('{{ formset.prefix }}-{{ forloop.counter0 }}');
        {% endfor %}

        panel.updateMoveButtonDisabledStates();
    });
})();
