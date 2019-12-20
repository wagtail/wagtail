{% load l10n %}
{% load wagtailadmin_tags %}
(function() {
    var panel = InlinePanel({
        formsetPrefix: "id_{{ self.formset.prefix }}",
        emptyChildFormPrefix: "{{ self.empty_child.form.prefix }}",
        canOrder: {% if can_order %}true{% else %}false{% endif %},
        maxForms: {{ self.formset.max_num|unlocalize }}
    });

    {% for child in self.children %}
        panel.initChildControls("{{ child.form.prefix }}");
    {% endfor %}
    panel.setHasContent();
    panel.updateMoveButtonDisabledStates();
    panel.updateAddButtonState();
})();
