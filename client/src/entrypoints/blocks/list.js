import $ from 'jquery';

// eslint-disable-next-line func-names
window.ListBlock = function (opts) {
  /* contents of 'opts':
          definitionPrefix (required)
          childInitializer (optional) - JS initializer function for each child
      */
  const listMemberTemplate = $('#' + opts.definitionPrefix + '-newmember').text();

  // eslint-disable-next-line func-names
  return function (elementPrefix) {
    // eslint-disable-next-line no-undef, new-cap
    const sequence = Sequence({
      prefix: elementPrefix,
      maxNumChildBlocks: Infinity,
      onInitializeMember(sequenceMember) {
        /* initialize child block's JS behaviour */
        if (opts.childInitializer) {
          opts.childInitializer(sequenceMember.prefix + '-value');
        }

        /* initialise delete button */
        $('#' + sequenceMember.prefix + '-delete').on('click', () => {
          sequenceMember.delete();
        });

        /* initialise move up/down buttons */
        $('#' + sequenceMember.prefix + '-moveup').on('click', () => {
          sequenceMember.moveUp();
        });

        $('#' + sequenceMember.prefix + '-movedown').on('click', () => {
          sequenceMember.moveDown();
        });
      },

      onEnableMoveUp(sequenceMember) {
        $('#' + sequenceMember.prefix + '-moveup').removeClass('disabled');
      },

      onDisableMoveUp(sequenceMember) {
        $('#' + sequenceMember.prefix + '-moveup').addClass('disabled');
      },

      onEnableMoveDown(sequenceMember) {
        $('#' + sequenceMember.prefix + '-movedown').removeClass('disabled');
      },

      onDisableMoveDown(sequenceMember) {
        $('#' + sequenceMember.prefix + '-movedown').addClass('disabled');
      }
    });

    /* initialize 'add' button */
    $('#' + elementPrefix + '-add').on('click', () => {
      sequence.insertMemberAtEnd(listMemberTemplate);
    });
  };
};
