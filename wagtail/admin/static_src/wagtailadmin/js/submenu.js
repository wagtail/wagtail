$(function() {
    $('.nav-main .submenu-trigger').on('click', function() {
        if ($(this).closest('li').find('.nav-submenu').length) {

            // Close other active submenus first, if any
            var hasC = $(this).closest('li').find('.nav-submenu').length > 0;
            if ($(this).closest('li').parent().parent().hasClass('nav-main')) {
                hasC = false;
            }

            if (hasC) {
                $(this).closest('li').siblings('.submenu-active').removeClass('submenu-active');
            }

            if ($('.nav-wrapper.submenu-active').length && !$(this).closest('li').hasClass('submenu-active') && !hasC) {
                $('.nav-main .submenu-active, .nav-wrapper').removeClass('submenu-active');
            }

            $(this).closest('li').toggleClass('submenu-active');
            if (!$('.nav-wrapper').hasClass('submenu-active')) {
                $('.nav-wrapper').addClass('submenu-active');
            }
            return false;
        }
    });

    $(document).on('keydown click', function(e) {
        if ($('.nav-wrapper.submenu-active').length && (e.keyCode == 27 || !e.keyCode)) {
            $('.nav-main .submenu-active, .nav-wrapper').removeClass('submenu-active');
        }
    });
});
