$(function() {
    var $switcher = $('form#settings-site-switch select');
    if (!$switcher.length) return;

    var initial = $switcher.val();
    $switcher.on('change', function() {
        var url = $switcher.val();
        if (url != initial) {
            window.location = url;
        }
    });
});
