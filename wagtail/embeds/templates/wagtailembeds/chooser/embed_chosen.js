function(modal) {
    modal.respond('embedChosen', '{{ embed_html|escapejs }}');
    modal.close();
}