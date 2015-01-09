(function($) {
    window.ListBlock = function(opts) {
        /* contents of 'opts':
            definitionPrefix (required)
            childInitializer (optional) - JS initializer function for each child
        */
        var listMemberTemplate = $('#' + opts.definitionPrefix + '-newmember').text();

        return function(elementPrefix) {
            var sequence = Sequence({
                'prefix': elementPrefix,
                'onInitializeMember': function(sequenceMember) {
                    /* initialize child block's JS behaviour */
                    if (opts.childInitializer) {
                        opts.childInitializer(sequenceMember.prefix + '-value');
                    }

                    /* initialise delete button */
                    $('#' + sequenceMember.prefix + '-delete').click(function() {
                        sequenceMember.delete();
                    });
                }
            });

            /* initialize 'add' button */
            $('#' + elementPrefix + '-add').click(function() {
                sequence.insertMemberAtEnd(listMemberTemplate);
            });
        };
    };
})(jQuery);
