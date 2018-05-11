function(modal) {
    modal.respond('embedChosen', '{{ embed_html|escapejs }}', {{ embed_json|safe }});
    modal.close();
}