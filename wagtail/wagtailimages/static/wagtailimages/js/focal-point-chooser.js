function createFocalPointCooser($chooser) {
    var $chosenText = $('.chosen-text', $chooser);
    var $focalPointX = $('input.focal_point_x', $chooser);
    var $focalPointY = $('input.focal_point_y', $chooser);
    var $focalPointWidth = $('input.focal_point_width', $chooser);
    var $focalPointHeight = $('input.focal_point_height', $chooser);
    var chooserUrl = $chooser.data('chooserUrl');

    $('.action-choose', $chooser).click(function() {
        if (!$chooser.hasClass('blank')) {
            window.focalPointChooserInitial = {
                x: $focalPointX.val(),
                y: $focalPointY.val(),
                w: $focalPointWidth.val(),
                h: $focalPointHeight.val(),
            }
        } else {
            window.focalPointChooserInitial = undefined;
        }

        ModalWorkflow({
            'url': chooserUrl,
            'responses': {
                'focalPointChosen': function(focalPointData) {
                    $focalPointX.val(focalPointData.x);
                    $focalPointY.val(focalPointData.y);
                    $focalPointWidth.val(focalPointData.w);
                    $focalPointHeight.val(focalPointData.h);

                    $chosenText.text(focalPointData.x + ", " + focalPointData.y + " " + focalPointData.w + "x" + focalPointData.h);

                    $chooser.removeClass('blank');
                }
            }
        });
    });

    $('.action-clear', $chooser).click(function() {
        $focalPointX.val('');
        $focalPointY.val('');
        $focalPointWidth.val('');
        $focalPointHeight.val('');

        $chooser.addClass('blank');
    });
}

$(function() {
    $('.focal-point-chooser').each(function() {
        createFocalPointCooser($(this));
    });
});
