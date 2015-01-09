(function($) {
    window.StreamBlock = function(opts) {
        /* Fetch the HTML template strings to be used when adding a new block of each type.
        Also reorganise the opts.childBlocks list into a lookup by name
        */
        var listMemberTemplates = {};
        var childBlocksByName = {};
        for (var i = 0; i < opts.childBlocks.length; i++) {
            var childBlock = opts.childBlocks[i];
            childBlocksByName[childBlock.name] = childBlock;
            var template = $('#' + opts.definitionPrefix + '-newmember-' + childBlock.name).text();
            listMemberTemplates[childBlock.name] = template;
        }

        return function(elementPrefix) {
            var sequence = Sequence({
                'prefix': elementPrefix,
                'onInitializeMember': function(sequenceMember) {
                    /* initialize child block's JS behaviour */
                    var blockTypeName = $('#' + sequenceMember.prefix + '-type').val();
                    var blockOpts = childBlocksByName[blockTypeName];
                    if (blockOpts.initializer) {
                        /* the child block's own elements have the prefix '{list member prefix}-value' */
                        blockOpts.initializer(sequenceMember.prefix + '-value');
                    }

                    /* initialize delete button */
                    $('#' + sequenceMember.prefix + '-delete').click(function() {
                        sequenceMember.delete();
                    });

                    /* initialize 'prepend new block' buttons */
                    function initializeAppendButton(childBlock) {
                        var template = listMemberTemplates[childBlock.name];
                        $('#' + sequenceMember.prefix + '-add-' + childBlock.name).click(function() {
                            sequenceMember.appendMember(template);
                        });
                    }
                    for (var i = 0; i < opts.childBlocks.length; i++) {
                        initializeAppendButton(opts.childBlocks[i]);
                    }
                }
            });

            /* initialize header menu */
            function initializePrependButton(childBlock) {
                var template = listMemberTemplates[childBlock.name];
                $('#' + elementPrefix + '-before-add-' + childBlock.name).click(function() {
                    sequence.insertMemberAtStart(template);
                });
            }
            for (var i = 0; i < opts.childBlocks.length; i++) {
                initializePrependButton(opts.childBlocks[i]);
            }
        };
    };
})(jQuery);
