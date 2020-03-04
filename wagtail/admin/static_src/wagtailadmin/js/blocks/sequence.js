/*

Operations on a sequence of items, common to both ListBlock and StreamBlock.

These assume the presence of a container element named "{prefix}-container" for each list item, and
certain hidden fields such as "{prefix}-deleted" as defined in sequence_member.html, but make no assumptions
about layout or visible controls within the block.

For example, they don't assume the presence of a 'delete' button - it's up to the specific subclass
(list.js / stream.js) to attach this to the SequenceMember.delete method.

CODE FOR SETTING UP SPECIFIC UI WIDGETS, SUCH AS DELETE BUTTONS OR MENUS, DOES NOT BELONG HERE.

*/
(function($) {
    window.SequenceMember = function(sequence, prefix) {
        var self = {};
        self.prefix = prefix;
        self.container = $('#' + self.prefix + '-container');

        var indexField = $('#' + self.prefix + '-order');

        self.delete = function() {
            sequence.deleteMember(self);
        };

        self.prependMember = function(template) {
            sequence.insertMemberBefore(self, template);
        };

        self.appendMember = function(template) {
            sequence.insertMemberAfter(self, template);
        };

        self.moveUp = function() {
            sequence.moveMemberUp(self);
        };

        self.moveDown = function() {
            sequence.moveMemberDown(self);
        };

        self._markDeleted = function() {
            /* set this list member's hidden 'deleted' flag to true */
            $('#' + self.prefix + '-deleted').val('1');
            /* hide the list item */
            self.container.slideUp().dequeue().fadeOut();
        };

        self._markAdded = function() {
            self.container.hide();
            self.container.slideDown();

            // focus first suitable input found
            setTimeout(function() {
              var $input = $('.input', self.container);
              var $firstField = $('input, textarea, [data-hallo-editor], [data-draftail-input]', $input).first();

              if ($firstField.is('[data-draftail-input]')) {
                $firstField.get(0).draftailEditor.focus();
              } else {
                $firstField.trigger('focus');
              }
            }, 250);
        };

        self.getIndex = function() {
            return parseInt(indexField.val(), 10);
        };

        self.setIndex = function(i) {
            indexField.val(i);
        };

        return self;
    };

    window.Sequence = function(opts) {
        var self = {};
        var list = $('#' + opts.prefix + '-list');
        var countField = $('#' + opts.prefix + '-count');
        /* NB countField includes deleted items; for the count of non-deleted items, use members.length */
        var members = [];

        self.getCount = function() {
            return parseInt(countField.val(), 10);
        };

        function getNewMemberPrefix() {
            /* Update the counter and use it to create a prefix for the new list member */
            var newIndex = self.getCount();
            countField.val(newIndex + 1);
            return opts.prefix + '-' + newIndex;
        }

        function postInsertMember(newMember) {
            /* run any supplied initializer functions */
            if (opts.onInitializeMember) {
                opts.onInitializeMember(newMember);
            }

            var index = newMember.getIndex();
            if (index === 0) {
                /* first item should have 'move up' disabled */
                if (opts.onDisableMoveUp) opts.onDisableMoveUp(newMember);
            } else {
                if (opts.onEnableMoveUp) opts.onEnableMoveUp(newMember);
            }

            if (index === (members.length - 1)) {
                /* last item should have 'move down' disabled */
                if (opts.onDisableMoveDown) opts.onDisableMoveDown(newMember);
            } else {
                if (opts.onEnableMoveDown) opts.onEnableMoveDown(newMember);
            }

            newMember._markAdded();
        }

        function elementFromTemplate(template, newPrefix) {
            /* generate a jquery object ready to be inserted into the list, based on the passed HTML template string.
            '__PREFIX__' will be substituted with newPrefix, and script tags escaped as <-/script> will be un-escaped */
            return $(template.replace(/__PREFIX__/g, newPrefix).replace(/<-(-*)\/script>/g, '<$1/script>'));
        }

        self.insertMemberBefore = function(otherMember, template) {
            var newMemberPrefix = getNewMemberPrefix();

            /* Create the new list member element with the real prefix substituted in */
            var elem = elementFromTemplate(template, newMemberPrefix);
            otherMember.container.before(elem);
            var newMember = SequenceMember(self, newMemberPrefix);
            var index = otherMember.getIndex();

            /* bump up index of otherMember and subsequent members */
            for (var i = index; i < members.length; i++) {
                members[i].setIndex(i + 1);
            }

            members.splice(index, 0, newMember);
            newMember.setIndex(index);

            postInsertMember(newMember);

            if (index === 0 && opts.onEnableMoveUp) {
                /* other member can now move up */
                opts.onEnableMoveUp(otherMember);
            }

            return newMember;
        };

        self.insertMemberAfter = function(otherMember, template) {
            var newMemberPrefix = getNewMemberPrefix();

            /* Create the new list member element with the real prefix substituted in */
            var elem = elementFromTemplate(template, newMemberPrefix);
            otherMember.container.after(elem);
            var newMember = SequenceMember(self, newMemberPrefix);
            var index = otherMember.getIndex() + 1;

            /* bump up index of subsequent members */
            for (var i = index; i < members.length; i++) {
                members[i].setIndex(i + 1);
            }

            members.splice(index, 0, newMember);
            newMember.setIndex(index);

            postInsertMember(newMember);

            if (index === (members.length - 1) && opts.onEnableMoveDown) {
                /* other member can now move down */
                opts.onEnableMoveDown(otherMember);
            }

            return newMember;
        };

        self.insertMemberAtStart = function(template) {
            /* NB we can't just do
                self.insertMemberBefore(members[0], template)
            because that won't work for initially empty lists
            */
            var newMemberPrefix = getNewMemberPrefix();

            /* Create the new list member element with the real prefix substituted in */
            var elem = elementFromTemplate(template, newMemberPrefix);
            list.prepend(elem);
            var newMember = SequenceMember(self, newMemberPrefix);

            /* bump up index of all other members */
            for (var i = 0; i < members.length; i++) {
                members[i].setIndex(i + 1);
            }

            members.unshift(newMember);
            newMember.setIndex(0);

            postInsertMember(newMember);

            if (members.length > 1 && opts.onEnableMoveUp) {
                /* previous first member can now move up */
                opts.onEnableMoveUp(members[1]);
            }

            return newMember;
        };

        self.insertMemberAtEnd = function(template) {
            var newMemberPrefix = getNewMemberPrefix();

            /* Create the new list member element with the real prefix substituted in */
            var elem = elementFromTemplate(template, newMemberPrefix);
            list.append(elem);
            var newMember = SequenceMember(self, newMemberPrefix);

            newMember.setIndex(members.length);
            members.push(newMember);

            postInsertMember(newMember);

            if (members.length > 1 && opts.onEnableMoveDown) {
                /* previous last member can now move down */
                opts.onEnableMoveDown(members[members.length - 2]);
            }

            return newMember;
        };

        self.deleteMember = function(member) {
            var index = member.getIndex();
            /* reduce index numbers of subsequent members */
            for (var i = index + 1; i < members.length; i++) {
                members[i].setIndex(i - 1);
            }
            /* remove from the 'members' list */
            members.splice(index, 1);
            member._markDeleted();

            if (index === 0 && members.length > 0 && opts.onDisableMoveUp) {
                /* deleting the first member; the new first member cannot move up now */
                opts.onDisableMoveUp(members[0]);
            }

            if (index === members.length && members.length > 0 && opts.onDisableMoveDown) {
                /* deleting the last member; the new last member cannot move down now */
                opts.onDisableMoveDown(members[members.length - 1]);
            }
        };

        self.moveMemberUp = function(member) {
            var oldIndex = member.getIndex();
            if (oldIndex > 0) {
                var newIndex = oldIndex - 1;
                var swappedMember = members[newIndex];

                members[newIndex] = member;
                member.setIndex(newIndex);

                members[oldIndex] = swappedMember;
                swappedMember.setIndex(oldIndex);

                member.container.insertBefore(swappedMember.container);

                if (newIndex === 0) {
                    /*
                    member is now the first member and cannot move up further;
                    swappedMember is no longer the first member, and CAN move up
                    */
                    if (opts.onDisableMoveUp) opts.onDisableMoveUp(member);
                    if (opts.onEnableMoveUp) opts.onEnableMoveUp(swappedMember);
                }

                if (oldIndex === (members.length - 1)) {
                    /*
                    member was previously the last member, and can now move down;
                    swappedMember is now the last member, and cannot move down
                    */
                    if (opts.onEnableMoveDown) opts.onEnableMoveDown(member);
                    if (opts.onDisableMoveDown) opts.onDisableMoveDown(swappedMember);
                }
            }
        };

        self.moveMemberDown = function(member) {
            var oldIndex = member.getIndex();
            if (oldIndex < (members.length - 1)) {
                var newIndex = oldIndex + 1;
                var swappedMember = members[newIndex];

                members[newIndex] = member;
                member.setIndex(newIndex);

                members[oldIndex] = swappedMember;
                swappedMember.setIndex(oldIndex);

                member.container.insertAfter(swappedMember.container);

                if (newIndex === (members.length - 1)) {
                    /*
                    member is now the last member and cannot move down further;
                    swappedMember is no longer the last member, and CAN move down
                    */
                    if (opts.onDisableMoveDown) opts.onDisableMoveDown(member);
                    if (opts.onEnableMoveDown) opts.onEnableMoveDown(swappedMember);
                }

                if (oldIndex === 0) {
                    /*
                    member was previously the first member, and can now move up;
                    swappedMember is now the first member, and cannot move up
                    */
                    if (opts.onEnableMoveUp) opts.onEnableMoveUp(member);
                    if (opts.onDisableMoveUp) opts.onDisableMoveUp(swappedMember);
                }
            }
        };

        /* initialize initial list members */
        var count = self.getCount();
        for (var i = 0; i < count; i++) {
            var memberPrefix = opts.prefix + '-' + i;
            var sequenceMember = SequenceMember(self, memberPrefix);
            members[i] = sequenceMember;
            if (opts.onInitializeMember) {
                opts.onInitializeMember(sequenceMember);
            }

            if (i === 0) {
                /* first item should have 'move up' disabled */
                if (opts.onDisableMoveUp) opts.onDisableMoveUp(sequenceMember);
            } else {
                if (opts.onEnableMoveUp) opts.onEnableMoveUp(sequenceMember);
            }

            if (i === (count - 1)) {
                /* last item should have 'move down' disabled */
                if (opts.onDisableMoveDown) opts.onDisableMoveDown(sequenceMember);
            } else {
                if (opts.onEnableMoveDown) opts.onEnableMoveDown(sequenceMember);
            }
        }

        return self;
    };
})(jQuery);
