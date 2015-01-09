(function($) {
    window.Chooser = function(definitionPrefix) {
        return function(elementPrefix) {
            $('#' + elementPrefix + '-button').click(function() {
                alert('hello, I am a chooser for ' + elementPrefix + ', which is of type ' + definitionPrefix);
            });
        };
    };
})(jQuery);
