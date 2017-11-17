function(modal) {
    modal.respond('snippetChosen', {{ snippet_json|safe }});
    modal.close();
}