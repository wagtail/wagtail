$(function() {
    $('.image-url-generator').each(function() {
        var $this = $(this);
        var $form = $this.find('form');
        var $filterMethodField = $form.find('select#id_filter_method');
        var $widthField = $form.find('input#id_width');
        var $heightField = $form.find('input#id_height');
        var $result = $this.find('div.result');

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
                })
                .fail(function(data) {
                    $result.text(data.responseJSON['error']);
                });
        }

        $form.change(formChangeHandler);
        $form.keyup(formChangeHandler);
        formChangeHandler();
    });
});
