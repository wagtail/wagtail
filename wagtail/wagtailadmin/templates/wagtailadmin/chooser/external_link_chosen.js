function(modal) {
    modal.respond('pageChosen', {
        'url': '{{ url|escapejs }}',
        'title': '{{ link_text|escapejs }}',
        'rel': '{{ rel|escapejs }}',
        'target': '{{ target|escapejs }}'
    });
    modal.close();
}
