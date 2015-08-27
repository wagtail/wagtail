function(modal) {
    modal.respond('linkChosen', {
        'type': '{{ type|escapejs }}',
        'url': '{{ url|escapejs }}',
        'title': '{{ link_text|escapejs }}'
    });
    modal.close();
}
