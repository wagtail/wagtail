$(function(){
    var $explorer = $('#explorer');
    var $body = $('body');

    // Dynamically load menu on request.
    $(document).on('click', '.dl-trigger', function(){
        var $this = $(this);
        
        // Close all submenus
        $('.nav-main .submenu-active, .nav-wrapper').removeClass('submenu-active');

        if($explorer.data('dlmenu') && $explorer.dlmenu('isOpen')){
            // if it's already open, allow the menu plugin to close it
            return false;
        }else{
            if(!$explorer.children().length){
                $this.addClass('icon-spinner');
                $explorer.load($this.data('explorer-menu-url'), function() {
                    $this.removeClass('icon-spinner');

                    $explorer.addClass('dl-menuwrapper').dlmenu({
                        animationClasses : {
                            classin : 'dl-animate-in-2',
                            classout : 'dl-animate-out-2'
                        }
                    });
                    $explorer.dlmenu('openMenu');
                });
            }else{
                $explorer.dlmenu('openMenu');
            }
        }
        return false;
    });

    // Close menu on ESC key
    $(document).on('keydown click', function(e){
        if($explorer.data('dlmenu') && $explorer.dlmenu('isOpen') && (e.keyCode == 27 || !e.keyCode)){
            $explorer.dlmenu('closeMenu');
        }
    });
});
