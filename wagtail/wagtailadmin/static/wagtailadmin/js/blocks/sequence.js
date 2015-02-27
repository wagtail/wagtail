/* Operations on a sequence of items, common to both ListBlock and StreamBlock.
These assume the presence of a container element named "{prefix}-container" for each list item, and
certain hidden fields such as "{prefix}-deleted" as defined in sequence_member.html, but make no assumptions
about layout or visible controls within the block. 
For example, they don't assume the presence of a 'delete' button - it's up to the specific subclass
(list.js / stream.js) to attach this to the SequenceMember.delete method.
*/
(function($) {
    window.SequenceMember = function(sequence, prefix) {
        var self = {};
        self.prefix = prefix;
        self.container = $('#' + self.prefix + '-container');
        self.menu = $('> .stream-menu', self.container);

        var indexField = $('#' + self.prefix + '-order');

        self.menu.click(function(e){
            e.preventDefault();
            self.toggleMenu();
        });

        self.delete = function() {
            sequence.deleteMember(self);
        };
        self.prependMember = function(template) {
            sequence.insertMemberBefore(self, template);
        };
        self.appendMember = function(template) {
            sequence.insertMemberAfter(self, template);
        };
        self._markDeleted = function() {
            /* set this list member's hidden 'deleted' flag to true */
            $('#' + self.prefix + '-deleted').val('1');
            /* hide the list item */
            self.container.fadeOut();
        };
        self._markAdded = function() {
            self.container.hide();
            self.container.slideDown();

            self.hideMenu();

            // focus first suitable input found
            var timeout = setTimeout(function(){
                $('.input input,.input textarea,.input .richtext', self.container).first().focus();
            }, 10);
        };
        self.getIndex = function() {
            return parseInt(indexField.val(), 10);
        };
        self.setIndex = function(i) {
            indexField.val(i);
        };

        self.toggleMenu = function(){
            if(self.menu.hasClass('stream-menu-closed')){
                self.showMenu();
            } else {
                self.hideMenu();
            }
        };
        self.showMenu = function(){
            self.menu.removeClass('stream-menu-closed');
        };
        self.hideMenu = function(){
            self.menu.addClass('stream-menu-closed');
        };

        return self;
    };
    window.Sequence = function(opts) {
        var self = {};
        var list = $('#' + opts.prefix + '-list');
        var countField = $('#' + opts.prefix + '-count');
        /* NB countField includes deleted items; for the count of non-deleted items, use members.length */
        var members = [];
        self.menu = countField.siblings('.stream-menu');

        self.menu.click(function(e){
            e.preventDefault();
            self.toggleMenu();
        });

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

            newMember._markAdded();
        }

        function elementFromTemplate(template, newPrefix) {
            /* generate a jquery object ready to be inserted into the list, based on the passed HTML template string.
            '__PREFIX__' will be substituted with newPrefix, and script tags escaped as <-/script> will be un-escaped */
            return $(template.replace(/__PREFIX__/g, newPrefix).replace(/<-(-*)\/script>/g, '<$1/script>'));
        }

        self.insertMemberBefore = function(otherMember, template) {
            newMemberPrefix = getNewMemberPrefix();

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

            return newMember;
        };

        self.insertMemberAfter = function(otherMember, template) {
            newMemberPrefix = getNewMemberPrefix();

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

            return newMember;
        };

        self.insertMemberAtStart = function(template) {
            /* NB we can't just do
                self.insertMemberBefore(members[0], template)
            because that won't work for initially empty lists
            */
            newMemberPrefix = getNewMemberPrefix();

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

            return newMember;
        };

        self.insertMemberAtEnd = function(template) {
            newMemberPrefix = getNewMemberPrefix();

            /* Create the new list member element with the real prefix substituted in */
            var elem = elementFromTemplate(template, newMemberPrefix);
            list.append(elem);
            var newMember = SequenceMember(self, newMemberPrefix);

            newMember.setIndex(members.length);
            members.push(newMember);

            postInsertMember(newMember);

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
        };

        self.toggleMenu = function(){
            if(self.menu.hasClass('stream-menu-closed')){
                self.showMenu();
            } else {
                self.hideMenu();
            }
        };
        
        self.showMenu = function(){
            self.menu.removeClass('stream-menu-closed');
        };

        self.hideMenu = function(){
            self.menu.addClass('stream-menu-closed');
        };


        /* initialize initial list members */
        for (var i = 0; i < self.getCount(); i++) {
            var memberPrefix = opts.prefix + '-' + i;
            var sequenceMember = SequenceMember(self, memberPrefix);
            members[i] = sequenceMember;
            if (opts.onInitializeMember) {
                opts.onInitializeMember(sequenceMember);
            }
        }

        return self;
    };
})(jQuery);
