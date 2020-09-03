(function($) {
    var StreamBlockMenu = function(opts) {
        /*
        Helper object to handle the menu of available block types.
        Options:
        childBlocks: list of block definitions (same as passed to StreamBlock)
        id: ID of the container element (the one around 'c-sf-add-panel')
        onChooseBlock: callback fired when a block type is chosen -
            the corresponding childBlock is passed as a parameter
        */
        var self = {};
        self.container = $('#' + opts.id);
        self.openCloseButton = $('#' + opts.id + '-openclose');

        if (self.container.hasClass('stream-menu-closed')) {
            self.container.hide();
        }

        self.show = function() {
            self.container.slideDown();
            self.container.removeClass('stream-menu-closed');
            self.container.attr('aria-hidden', 'false');
            self.openCloseButton.addClass('c-sf-add-button--close');
        };

        self.hide = function() {
            self.container.slideUp();
            self.container.addClass('stream-menu-closed');
            self.container.attr('aria-hidden', 'true');
            self.openCloseButton.removeClass('c-sf-add-button--close');
        };

        self.addFirstBlock = function() {
            if (opts.onChooseBlock) opts.onChooseBlock(opts.childBlocks[0]);
        };

        self.toggle = function() {
            if (self.container.hasClass('stream-menu-closed')) {
                if (opts.childBlocks.length == 1) {
                    /* If there's only one block type, add it automatically */
                    self.addFirstBlock();
                } else {
                    self.show();
                }
            } else {
                self.hide();
            }
        };

        /* set up show/hide on click behaviour */
        self.openCloseButton.on('click', function(e) {
            e.preventDefault();
            self.toggle();
        });

        /* set up button behaviour */
        $.each(opts.childBlocks, function(i, childBlock) {
            var button = self.container.find('.action-add-block-' + childBlock.name);
            button.on('click', function() {
                if (opts.onChooseBlock) opts.onChooseBlock(childBlock);
                self.hide();
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
                prefix: elementPrefix,
                maxNumChildBlocks: opts.maxNumChildBlocks,
                onInitializeMember: function(sequenceMember) {
                    /* initialize child block's JS behaviour */
                    var blockTypeName = $('#' + sequenceMember.prefix + '-type').val();
                    var blockOpts = childBlocksByName[blockTypeName];
                    if (blockOpts.initializer) {
                        /* the child block's own elements have the prefix '{list member prefix}-value' */
                        blockOpts.initializer(sequenceMember.prefix + '-value');
                    }

                    /* initialize delete button */
                    $('#' + sequenceMember.prefix + '-delete').on('click', function() {
                        sequenceMember.delete();
                    });

                    /* initialise move up/down buttons */
                    $('#' + sequenceMember.prefix + '-moveup').on('click', function() {
                        sequenceMember.moveUp();
                    });

                    $('#' + sequenceMember.prefix + '-movedown').on('click', function() {
                        sequenceMember.moveDown();
                    });

                    /* Set up the 'append a block' menu that appears after the block */
                    StreamBlockMenu({
                        childBlocks: opts.childBlocks,
                        id: sequenceMember.prefix + '-appendmenu',
                        onChooseBlock: function(childBlock) {
                            var template = listMemberTemplates[childBlock.name];
                            sequenceMember.appendMember(template);
                        }
                    });
                },

                onEnableMoveUp: function(sequenceMember) {
                    $('#' + sequenceMember.prefix + '-moveup').removeClass('disabled');
                },

                onDisableMoveUp: function(sequenceMember) {
                    $('#' + sequenceMember.prefix + '-moveup').addClass('disabled');
                },

                onEnableMoveDown: function(sequenceMember) {
                    $('#' + sequenceMember.prefix + '-movedown').removeClass('disabled');
                },

                onDisableMoveDown: function(sequenceMember) {
                    $('#' + sequenceMember.prefix + '-movedown').addClass('disabled');
                },
                
                onDisableAdd: function(members) {
                    for (var i = 0; i < members.length; i++){
                        $('#' + members[i].prefix + '-appendmenu-openclose')
                            .removeClass('c-sf-add-button--visible').delay(300).slideUp()
                    }
                    $('#' + elementPrefix + '-prependmenu-openclose')
                        .removeClass('c-sf-add-button--visible').delay(300).slideUp()
                },

                onEnableAdd: function(members) {
                    for (var i = 0; i < members.length; i++){
                        
                        $('#' + members[i].prefix + '-appendmenu-openclose')
                            .addClass('c-sf-add-button--visible').delay(300).slideDown()
                    }
                    $('#' + elementPrefix + '-prependmenu-openclose')
                        .addClass('c-sf-add-button--visible').delay(300).slideDown()
                }
            });

            /* Set up the 'prepend a block' menu that appears above the first block in the sequence */
            StreamBlockMenu({
                childBlocks: opts.childBlocks,
                id: elementPrefix + '-prependmenu',
                onChooseBlock: function(childBlock) {
                    var template = listMemberTemplates[childBlock.name];
                    sequence.insertMemberAtStart(template);
                }
            });
        };
    };
})(jQuery);
