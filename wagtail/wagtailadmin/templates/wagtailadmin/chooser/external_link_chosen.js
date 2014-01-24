function(modal) {
    modal.respond('pageChosen', {
        'url': '{{ url|escapejs }}',
        'title': '{{ link_text|escapejs }}'
    });
    modal.close();
}
