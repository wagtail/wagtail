function(modal) {
    modal.respond('embedChosen', '{{ embed_html|safe }}');
    modal.close();
}