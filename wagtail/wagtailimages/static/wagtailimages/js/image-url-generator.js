$(function() {
    $('.image-url-generator').each(function() {
        var $this = $(this);
        var $form = $this.find('form');
        var $filterMethodField = $form.find('select#id_filter_method');
        var $widthField = $form.find('input#id_width');
        var $heightField = $form.find('input#id_height');
        var $result = $this.find('div.result');
        var $preview = $this.find('img.preview');

        var generatorUrl = $this.data('generatorUrl');

        function formChangeHandler() {
            var filterSpec = $filterMethodField.val();

            if (filterSpec == 'original') {
                $widthField.prop('disabled', true);
                $heightField.prop('disabled', true);
            } else if (filterSpec == 'width') {
                $widthField.prop('disabled', false);
                $heightField.prop('disabled', true);
                filterSpec += '-' + $widthField.val();
            } else if (filterSpec == 'height') {
                $widthField.prop('disabled', true);
                $heightField.prop('disabled', false);
                filterSpec += '-' + $heightField.val();
            } else if (filterSpec == 'min' || filterSpec == 'max' || filterSpec == 'fill') {
                $widthField.prop('disabled', false);
                $heightField.prop('disabled', false);
                filterSpec += '-' + $widthField.val() + 'x' + $heightField.val();
            }

            // Fields with width and height
            $.getJSON(generatorUrl.replace('__filterspec__', filterSpec))
                .done(function(data) {
                    $result.text(data['url']);
                    $preview.attr('src', data['url']);
                })
                .fail(function(data) {
                    $result.text(data.responseJSON['error']);
                    $preview.attr('src', '');
                });
        }

        $form.change(formChangeHandler);
        $form.keyup(formChangeHandler);
        formChangeHandler();

        // When the user clicks the URL, automatically select the whole thing (for easier copying)
        $result.click(function() {
            if (document.selection) {
                document.selection.empty();

                var range = document.body.createTextRange();
                range.moveToElementText(this);
                range.select();
            } else if (window.getSelection) {
                window.getSelection().removeAllRanges();

                var range = document.createRange();
                range.selectNodeContents(this);
                window.getSelection().addRange(range);
            }
        });
    });
});
