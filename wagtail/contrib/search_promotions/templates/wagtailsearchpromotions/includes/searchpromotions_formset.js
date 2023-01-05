$(function () {
  // eslint-disable-next-line no-undef
  var panel = new InlinePanel({
    formsetPrefix: 'id_{{ formset.prefix }}',
    emptyChildFormPrefix: '{{ formset.empty_form.prefix }}',
    canOrder: true,
  });
});
