function createQueryChooser(id) {
    var chooserElement = $('#' + id + '-chooser');
    var input = $('#' + id);

    chooserElement.click(function() {
        var initialUrl = '{% url "wagtailsearch_queries_chooser" %}';

        ModalWorkflow({
            'url': initialUrl,
            'responses': {
                'queryChosen': function(queryData) {
                    input.val(queryData.querystring);
                }
            }
        });
    });
}
