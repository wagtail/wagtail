$(function(){
    // Dynamically load menu on request.
    $(document).on('click', '.dl-trigger', function(){
        var $this = $(this);
        var $explorer = $('#explorer');

        $this.addClass('icon-spinner');

        if(!$explorer.children().length){
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

        return false;
    });
});
