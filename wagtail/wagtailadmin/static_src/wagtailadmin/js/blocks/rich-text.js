(function($) {
    window.RichTextBlock = function(opts) {
        $('.widget-rich_text_area .richtext').tooltip({
            animation: false,
            title: function() {
                return $(this).attr('href');
            },
            trigger: 'hover',
            placement: 'bottom',
            selector: 'a'
        });
    };
})(jQuery);
