$(function() {
    $('.image-url-generator').each(function() {
        var $this = $(this);
        var $filter = $this.find('input.filter');
        var $result = $this.find('div.result');

        var generatorUrl = $this.data('generatorUrl');

        $filter.keyup(function() {
            $.getJSON(generatorUrl.replace('__filterspec__', $filter.val()))
                .done(function(data) {
                    $result.text(data['url']);
                })
                .fail(function(data) {
                    $result.text(data.responseJSON['error']);
                });
        });
    });
});
