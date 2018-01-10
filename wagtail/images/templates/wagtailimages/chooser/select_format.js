function(modal) {
    $('form', modal.body).on('submit', function() {
        var formdata = new FormData(this);

        $.post(this.action, $(this).serialize(), function(response){
            modal.loadResponseText(response);
        }, 'text');

        return false;
    });
}
