function(modal) {
    $('form.embed-form', modal.body).submit(function() {
        var formdata = new FormData(this);

        $.ajax({
            url: this.action,
            data: formdata,
            processData: false,
            contentType: false,
            type: 'POST',
            dataType: 'text',
            success: function(response){
                modal.loadResponseText(response);
            }
        });

        return false;
    });
    $('ul.embeds a.embed-choice').click(function(event){
        event.preventDefault();
        modal.loadUrl(this.href);
        return false;
    });
}
