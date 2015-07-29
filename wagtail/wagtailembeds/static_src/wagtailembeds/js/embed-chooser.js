function createEmbedChooser(id) {
    var chooserElement = $('#' + id + '-chooser');
    var embedTitle = chooserElement.find('.title');
    var previewImage = chooserElement.find('.preview-embed img');
    var input = $('#' + id);

    $('.action-choose', chooserElement).click(function() {
        ModalWorkflow({
            url: window.chooserUrls.embedsChooser,
            responses: {
                embedChosen: function(embed) {
                    input.val(embed.json.url);
                    embedTitle.text(embed.json.title);
                    if (embed.json.hasOwnProperty('thumbnail_url') && embed.json.thumbnail_url != null) {
                        previewImage.attr({
                            src: embed.json.thumbnail_url,
                            alt: embed.json.title
                        });
                    }
                    else {
                        // Should be setting provider default placeholder image, may be..
                        // could be a css class with svg icons too
                        previewImage.attr({
                            src: ''
                        });
                    }

                    chooserElement.removeClass('blank');
                }
            }
        });
    });

    $('.action-clear', chooserElement).click(function() {
        input.val('');
        chooserElement.addClass('blank');
    });
}
