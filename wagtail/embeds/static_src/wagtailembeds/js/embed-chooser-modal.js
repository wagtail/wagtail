EMBED_CHOOSER_MODAL_ONLOAD_HANDLERS = {
    'chooser': function(modal, jsonData) {
        $('form.embed-form', modal.body).on('submit', function() {
            var formdata = new FormData(this);

            $.ajax({
                url: this.action,
                data: formdata,
                processData: false,
                contentType: false,
                type: 'POST',
                dataType: 'text',
                success: modal.loadResponseText
            });

            return false;
        });
    },
    'embed_chosen': function(modal, jsonData) {
        modal.respond('embedChosen', jsonData.embed_html, jsonData.embed_data);
        modal.close();
    }
};
