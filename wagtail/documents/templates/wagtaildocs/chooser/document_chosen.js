function(modal) {
    modal.respond('documentChosen', {{ document_json|safe }});
    modal.close();
}
