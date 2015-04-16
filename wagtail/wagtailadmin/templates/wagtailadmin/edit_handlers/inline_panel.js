(function() {
    var children = JSON.parse('[{% for child in self.children %}"{{child.form.prefix}}"{% if not forloop.last %},{% endif %}{% endfor %}]');
    var panel = InlinePanel({
        formsetPrefix: 'id_{{ self.formset.prefix }}',
        emptyChildFormPrefix: '{{ self.empty_child.form.prefix }}',
        canOrder: '{% if can_order %}true{% endif %}' === 'true'
    });

    for (var i = 0; i < children.length; i++) {
        panel.initChildControls(children[i]);
    }

    panel.setHasContent();
    panel.updateMoveButtonDisabledStates();
})();
