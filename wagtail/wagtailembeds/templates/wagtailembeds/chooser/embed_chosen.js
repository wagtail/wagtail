function(modal) {
    modal.respond('embedChosen', {
        "html": '{{ embed_html|escapejs }}',
        "json": {{ embed_json|safe }}
    });
    modal.close();
}