function createQueryChooser(id) {
  var chooserElement = $('#' + id + '-chooser');
  var input = $('#' + id);

  chooserElement.on('click', function () {
    var initialUrl = '{% url "wagtailsearchpromotions:chooser" %}';

    ModalWorkflow({
      url: initialUrl,
      onload: QUERY_CHOOSER_MODAL_ONLOAD_HANDLERS,
      responses: {
        queryChosen: function (queryData) {
          input.val(queryData.querystring);
        },
      },
    });
  });
}
