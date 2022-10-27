$(function () {
  // eslint-disable-next-line no-undef
  var panel = InlinePanel({
    formsetPrefix: 'id_{{ formset.prefix }}',
    emptyChildFormPrefix: '{{ formset.empty_form.prefix }}',
    canOrder: true,
  });

  // {# Ensure eslint/prettier ignore the Django template syntax by treating them as comments, template for loop will still be executed by Django #}
  // {% for form in formset.forms %}
  panel.initChildControls('{{ formset.prefix }}-{{ forloop.counter0 }}');
  // {% endfor %}

  panel.updateMoveButtonDisabledStates();
});
