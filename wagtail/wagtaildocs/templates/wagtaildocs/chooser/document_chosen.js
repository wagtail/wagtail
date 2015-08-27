function(modal) {
    modal.respond('linkChosen', {{ document_json|safe }});
    modal.close();
}
