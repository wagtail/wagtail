function(modal) {
    var jcapi;

    function ajaxifyLinks (context) {
        $('.listing a', context).click(function() {
            modal.loadUrl(this.href);
            return false;
        });

        $('.pagination a', context).click(function() {
            var page = this.getAttribute("data-page");
            setPage(page);
            return false;
        });
    }

    ajaxifyLinks(modal.body);

    // Find image element
    var $image = $('.focal-point-chooser-image img');

    // Switch on Jcrop
    $image.Jcrop({}, function() {
        jcapi = this;
    });

    // Set initial select box
    if (window.focalPointChooserInitial) {
        var scaleX = {{ image.width }} / $image.width();
        var scaleY = {{ image.height }} / $image.height();

        var x = window.focalPointChooserInitial.x / scaleX;
        var y = window.focalPointChooserInitial.y / scaleY;
        var w = window.focalPointChooserInitial.w / scaleX;
        var h = window.focalPointChooserInitial.h / scaleY;

        jcapi.setSelect([
            x - w / 2,
            y - h / 2,
            x + w / 2,
            y + h / 2,
        ]);
    }

    $('a.choose-focal-point', modal.body).click(function() {
        var selectBox = jcapi.tellSelect();
        var scaleX = {{ image.width }} / $image.width();
        var scaleY = {{ image.height }} / $image.height();

        modal.respond('focalPointChosen', {
            x: Math.floor(scaleX * (selectBox.x + selectBox.x2) / 2),
            y: Math.floor(scaleY * (selectBox.y + selectBox.y2) / 2),
            w: Math.floor(scaleX * selectBox.w),
            h: Math.floor(scaleY * selectBox.h),
        });

        modal.close();

        return false;
    });

    $('#id_q').on('input', function() {
        clearTimeout($.data(this, 'timer'));
        var wait = setTimeout(search, 200);
        $(this).data('timer', wait);
    });
}