function(modal) {
    modal.respond('pageChosen', {{ result_json|safe }});
    modal.close();
}
