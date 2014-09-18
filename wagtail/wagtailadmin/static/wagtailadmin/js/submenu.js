$(function(){
    $('.nav-main .submenu-trigger').on('click', function(){
        if($(this).closest('li').find('.nav-submenu').length){
            $(this).closest('li').toggleClass('submenu-active');
            $('.nav-wrapper').toggleClass('submenu-active')
            return false
        }
    });

    $(document).on('keydown click', function(e){
        if($('.nav-wrapper.submenu-active').length){
            if(e.keyCode == 27 || !e.keyCode){
                $('.nav-main .submenu-active').removeClass('submenu-active');
                $('.nav-wrapper').toggleClass('submenu-active')
            }
        }
    });
});
