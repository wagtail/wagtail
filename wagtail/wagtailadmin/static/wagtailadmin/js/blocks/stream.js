(function($) {
    var StreamBlockMenu = function(opts) {
        /*
        Helper object to handle the menu of available block types.
        Options:
        childBlocks: list of block definitions (same as passed to StreamBlock)
        id: ID of the container element (the one with class="stream-menu")
        onChooseBlock: callback fired when a block type is chosen -
            the corresponding childBlock is passed as a parameter
        */
        var self = {};
        self.container = $('#' + opts.id);

        self.show = function(){
            self.container.removeClass('stream-menu-closed');
        };
        self.hide = function(){
            self.container.addClass('stream-menu-closed');
        };
        self.toggle = function(){
            if(self.container.hasClass('stream-menu-closed')){
                self.show();
            } else {
                self.hide();
            }
        };

        /* set up show/hide on click behaviour */
        self.container.click(function(e){
            e.preventDefault();
            self.toggle();
        });

        /* set up button behaviour */
        $.each(opts.childBlocks, function(i, childBlock) {
            var button = self.container.find('.action-add-block-' + childBlock.name);
            button.click(function() {
                if (opts.onChooseBlock) opts.onChooseBlock(childBlock);
            });
        });

        return self;
    };

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

                    /* Set up the 'append a block' menu that appears after the block */
                    StreamBlockMenu({
                        'childBlocks': opts.childBlocks,
                        'id': sequenceMember.prefix + '-appendmenu',
                        'onChooseBlock': function(childBlock) {
                            var template = listMemberTemplates[childBlock.name];
                            sequenceMember.appendMember(template);
                        }
                    });
                }
            });

            /* Set up the 'prepend a block' menu that appears above the first block in the sequence */
            StreamBlockMenu({
                'childBlocks': opts.childBlocks,
                'id': elementPrefix + '-prependmenu',
                'onChooseBlock': function(childBlock) {
                    var template = listMemberTemplates[childBlock.name];
                    sequence.insertMemberAtStart(template);
                }
            });
        };
    };
})(jQuery);
