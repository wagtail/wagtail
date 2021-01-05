/*

Operations on a sequence of items, common to both ListBlock and StreamBlock.

These assume the presence of a container element named "{prefix}-container" for each list item, and
certain hidden fields such as "{prefix}-deleted" as defined in sequence_member.html, but make no assumptions
about layout or visible controls within the block.

For example, they don't assume the presence of a 'delete' button - it's up to the specific subclass
(list.js / stream.js) to attach this to the SequenceMember.delete method.

CODE FOR SETTING UP SPECIFIC UI WIDGETS, SUCH AS DELETE BUTTONS OR MENUS, DOES NOT BELONG HERE.

*/

import $ from 'jquery';

// eslint-disable-next-line func-names
window.SequenceMember = function (sequence, prefix) {
  const self = {};
  self.prefix = prefix;
  self.container = $('#' + self.prefix + '-container');

  const indexField = $('#' + self.prefix + '-order');

  // eslint-disable-next-line func-names
  self.delete = function () {
    sequence.deleteMember(self);
  };

  // eslint-disable-next-line func-names
  self.prependMember = function (template) {
    sequence.insertMemberBefore(self, template);
  };

  // eslint-disable-next-line func-names
  self.appendMember = function (template) {
    sequence.insertMemberAfter(self, template);
  };

  // eslint-disable-next-line func-names
  self.moveUp = function () {
    sequence.moveMemberUp(self);
  };

  // eslint-disable-next-line func-names
  self.moveDown = function () {
    sequence.moveMemberDown(self);
  };

  // eslint-disable-next-line func-names
  self.markDeleted = function () {
    /* set this list member's hidden 'deleted' flag to true */
    $('#' + self.prefix + '-deleted').val('1');
    /* hide the list item */
    self.container.slideUp().dequeue().fadeOut();
  };

  // eslint-disable-next-line func-names
  self.markAdded = function () {
    self.container.hide();
    self.container.slideDown();

    // focus first suitable input found
    setTimeout(() => {
      const $input = $('.input', self.container);
      const $firstField = $('input, textarea, [data-hallo-editor], [data-draftail-input]', $input).first();

      if ($firstField.is('[data-draftail-input]')) {
        $firstField.get(0).draftailEditor.focus();
      } else {
        $firstField.trigger('focus');
      }
    }, 250);
  };

  // eslint-disable-next-line func-names
  self.getIndex = function () {
    return parseInt(indexField.val(), 10);
  };

  // eslint-disable-next-line func-names
  self.setIndex = function (i) {
    indexField.val(i);
  };

  return self;
};

// eslint-disable-next-line func-names
window.Sequence = function (opts) {
  const self = {};
  const list = $('#' + opts.prefix + '-list');
  const countField = $('#' + opts.prefix + '-count');
  /* NB countField includes deleted items; for the count of non-deleted items, use members.length */
  const members = [];

  // eslint-disable-next-line func-names
  self.getCount = function () {
    return parseInt(countField.val(), 10);
  };

  function getNewMemberPrefix() {
    /* Update the counter and use it to create a prefix for the new list member */
    const newIndex = self.getCount();
    countField.val(newIndex + 1);
    return opts.prefix + '-' + newIndex;
  }

  function postInsertMember(newMember) {
    /* run any supplied initializer functions */
    if (opts.onInitializeMember) {
      opts.onInitializeMember(newMember);
    }

    const index = newMember.getIndex();
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

    newMember.markAdded();

    if (members.length >= opts.maxNumChildBlocks && opts.onDisableAdd) {
      /* maximum block capacity has been reached */
      opts.onDisableAdd(members);
    }
  }

  function elementFromTemplate(template, newPrefix) {
    /* generate a jquery object ready to be inserted into the list, based on the passed HTML template string.
          '__PREFIX__' will be substituted with newPrefix, and script tags escaped as <-/script> will be un-escaped */
    return $(template.replace(/__PREFIX__/g, newPrefix).replace(/<-(-*)\/script>/g, '<$1/script>'));
  }

  // eslint-disable-next-line func-names
  self.insertMemberBefore = function (otherMember, template) {
    const newMemberPrefix = getNewMemberPrefix();

    /* Create the new list member element with the real prefix substituted in */
    const elem = elementFromTemplate(template, newMemberPrefix);
    otherMember.container.before(elem);
    // eslint-disable-next-line no-undef, new-cap
    const newMember = SequenceMember(self, newMemberPrefix);
    const index = otherMember.getIndex();

    /* bump up index of otherMember and subsequent members */
    for (let i = index; i < members.length; i++) {
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

  // eslint-disable-next-line func-names
  self.insertMemberAfter = function (otherMember, template) {
    const newMemberPrefix = getNewMemberPrefix();

    /* Create the new list member element with the real prefix substituted in */
    const elem = elementFromTemplate(template, newMemberPrefix);
    otherMember.container.after(elem);
    // eslint-disable-next-line no-undef, new-cap
    const newMember = SequenceMember(self, newMemberPrefix);
    const index = otherMember.getIndex() + 1;

    /* bump up index of subsequent members */
    for (let i = index; i < members.length; i++) {
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

  // eslint-disable-next-line func-names
  self.insertMemberAtStart = function (template) {
    /* NB we can't just do
              self.insertMemberBefore(members[0], template)
          because that won't work for initially empty lists
          */
    const newMemberPrefix = getNewMemberPrefix();

    /* Create the new list member element with the real prefix substituted in */
    const elem = elementFromTemplate(template, newMemberPrefix);
    list.prepend(elem);
    // eslint-disable-next-line no-undef, new-cap
    const newMember = SequenceMember(self, newMemberPrefix);

    /* bump up index of all other members */
    for (let i = 0; i < members.length; i++) {
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

  // eslint-disable-next-line func-names
  self.insertMemberAtEnd = function (template) {
    const newMemberPrefix = getNewMemberPrefix();

    /* Create the new list member element with the real prefix substituted in */
    const elem = elementFromTemplate(template, newMemberPrefix);
    list.append(elem);
    // eslint-disable-next-line no-undef, new-cap
    const newMember = SequenceMember(self, newMemberPrefix);

    newMember.setIndex(members.length);
    members.push(newMember);

    postInsertMember(newMember);

    if (members.length > 1 && opts.onEnableMoveDown) {
      /* previous last member can now move down */
      opts.onEnableMoveDown(members[members.length - 2]);
    }

    return newMember;
  };

  // eslint-disable-next-line func-names
  self.deleteMember = function (member) {
    const index = member.getIndex();
    /* reduce index numbers of subsequent members */
    for (let i = index + 1; i < members.length; i++) {
      members[i].setIndex(i - 1);
    }
    /* remove from the 'members' list */
    members.splice(index, 1);
    member.markDeleted();

    if (index === 0 && members.length > 0 && opts.onDisableMoveUp) {
      /* deleting the first member; the new first member cannot move up now */
      opts.onDisableMoveUp(members[0]);
    }

    if (index === members.length && members.length > 0 && opts.onDisableMoveDown) {
      /* deleting the last member; the new last member cannot move down now */
      opts.onDisableMoveDown(members[members.length - 1]);
    }

    if (members.length + 1 >= opts.maxNumChildBlocks && members.length < opts.maxNumChildBlocks && opts.onEnableAdd) {
      /* there is now capacity left for another block */
      opts.onEnableAdd(members);
    }
  };

  // eslint-disable-next-line func-names
  self.moveMemberUp = function (member) {
    const oldIndex = member.getIndex();
    if (oldIndex > 0) {
      const newIndex = oldIndex - 1;
      const swappedMember = members[newIndex];

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

  // eslint-disable-next-line func-names
  self.moveMemberDown = function (member) {
    const oldIndex = member.getIndex();
    if (oldIndex < (members.length - 1)) {
      const newIndex = oldIndex + 1;
      const swappedMember = members[newIndex];

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
  const count = self.getCount();
  for (let i = 0; i < count; i++) {
    const memberPrefix = opts.prefix + '-' + i;
    // eslint-disable-next-line no-undef, new-cap
    const sequenceMember = SequenceMember(self, memberPrefix);
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

  if (members.length >= opts.maxNumChildBlocks && opts.onDisableAdd) {
    /* block capacity is already reached on initialization */
    opts.onDisableAdd(members);
  }

  return self;
};
