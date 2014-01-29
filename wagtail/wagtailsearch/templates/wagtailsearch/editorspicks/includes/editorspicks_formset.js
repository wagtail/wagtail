(function() {
    function fixPrefix(str) {return str;}

    var panel = InlinePanel({
        formsetPrefix: fixPrefix("id_{{ formset.prefix }}"),
        emptyChildFormPrefix: fixPrefix("{{ formset.empty_form.prefix }}"),
        canOrder: true,

        onAdd: function(fixPrefix) {
            createPageChooser(fixPrefix('id_{{ formset.prefix }}-__prefix__-page'), 'wagtailcore.page', null);
        }
    });

    {% for form in formset.forms %}
        createPageChooser(fixPrefix('id_{{ formset.prefix }}-{{ forloop.counter0 }}-page'), 'wagtailcore.page', null);
        panel.initChildControls('{{ formset.prefix }}-{{ forloop.counter0 }}');
    {% endfor %}

    panel.updateMoveButtonDisabledStates();
})();