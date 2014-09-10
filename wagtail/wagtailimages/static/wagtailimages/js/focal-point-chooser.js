$(function() {
    var $chooser = $('div.focal-point-chooser');
    var $indicator = $('.current-focal-point-indicator', $chooser);
    var $image = $('img', $chooser);
    var $focalPointXField = $('input.focal_point_x');
    var $focalPointYField = $('input.focal_point_y');
    var $focalPointWidthField = $('input.focal_point_width');
    var $focalPointHeightField = $('input.focal_point_height');

    var originalWidth = $image.data('originalWidth');
    var originalHeight = $image.data('originalHeight');

    var focalPointXOriginal = $chooser.data('focalPointX');
    var focalPointYOriginal = $chooser.data('focalPointY');
    var focalPointWidthOriginal = $chooser.data('focalPointWidth');
    var focalPointHeightOriginal = $chooser.data('focalPointHeight');

    $image.Jcrop({
        trueSize: [originalWidth, originalHeight],
        onSelect: function(box) {
            var x = Math.floor((box.x + box.x2) / 2);
            var y = Math.floor((box.y + box.y2) / 2);
            var w = Math.floor(box.w);
            var h = Math.floor(box.h);

            $focalPointXField.val(x);
            $focalPointYField.val(y);
            $focalPointWidthField.val(w);
            $focalPointHeightField.val(h);
        },
        onRelease: function() {
            $focalPointXField.val(focalPointXOriginal);
            $focalPointYField.val(focalPointYOriginal);
            $focalPointWidthField.val(focalPointWidthOriginal);
            $focalPointHeightField.val(focalPointHeightOriginal);
        },
    });

    $indicator.css('left', ((focalPointXOriginal - focalPointWidthOriginal / 2) * 100 / originalWidth) + '%');
    $indicator.css('top', ((focalPointYOriginal - focalPointHeightOriginal / 2) * 100 / originalHeight) + '%');
    $indicator.css('width', (focalPointWidthOriginal * 100 / originalWidth) + '%');
    $indicator.css('height', (focalPointHeightOriginal * 100 / originalHeight) + '%');
});
