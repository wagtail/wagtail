(function($) {
    window.ListBlock = function(opts) {
        /* contents of 'opts':
            definitionPrefix (required)
            childInitializer (optional) - JS initializer function for each child
        */
        var listMemberTemplate = $('#' + opts.definitionPrefix + '-newmember').text();

        return function(elementPrefix) {
            var errorText = $('#' + elementPrefix + '-errors');
            var addButton = $('#' + elementPrefix + '-add');

            var sequence = Sequence({
                prefix: elementPrefix,
                onInitializeMember: function(sequenceMember) {
                    /* initialize child block's JS behaviour */
                    if (opts.childInitializer) {
                        opts.childInitializer(sequenceMember.prefix + '-value');
                    }

                    /* initialise delete button */
                    $('#' + sequenceMember.prefix + '-delete').click(function() {
                        sequenceMember.delete();
                    });

                    /* initialise move up/down buttons */
                    $('#' + sequenceMember.prefix + '-moveup').click(function() {
                        sequenceMember.moveUp();
                    });

                    $('#' + sequenceMember.prefix + '-movedown').click(function() {
                        sequenceMember.moveDown();
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
                }
            });

            var addMember = function() {
                sequence.insertMemberAtEnd(listMemberTemplate);
            }

            /* initialize 'add' button */
            addButton.click(addMember);

            function checkMinMax(){
              if (opts.max_num && sequence.getRealCount() >= opts.max_num) {
                  addButton.addClass('disabled');
                  addButton.unbind('click', addMember)
              } else {
                  addButton.removeClass('disabled');
                  /* unbind first to ensure we aren't binding multiple times */
                  addButton.unbind('click', addMember)
                  addButton.click(addMember);
              }

              if (opts.min_num && sequence.getRealCount() < opts.min_num){
                if (!$("#" +  elementPrefix + "-min-error").length) {
                  errorText.append(
                    "<div id=\"" + elementPrefix + "-min-error\" class=\"help-block help-critical\">" + opts.min_num + " or more items required</div>");
                }
              } else {
                $("#" +  elementPrefix + "-min-error").remove();
              }
            }

            checkMinMax(sequence);

            sequence.__postInsertMember = sequence._postInsertMember;
            sequence._postInsertMember = function(newMember){
              sequence.__postInsertMember(newMember);
              checkMinMax();
            }

            sequence._deleteMember = sequence.deleteMember;
            sequence.deleteMember = function(member){
              sequence._deleteMember(member);
              checkMinMax();
            }
        };
    };
})(jQuery);
