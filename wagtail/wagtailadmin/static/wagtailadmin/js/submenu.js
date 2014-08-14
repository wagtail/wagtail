$(function(){
    $('.nav-main li.submenu-trigger').each(function() {
        var submenuUl = $(this).find('> ul.nav-submenu');
        /* move submenuUl out of .nav-main */
        $('.nav-wrapper').append(submenuUl);

        $(this).find('> a').click(function() {
            submenuUl.toggle();
            return false;
        });
    });
});
