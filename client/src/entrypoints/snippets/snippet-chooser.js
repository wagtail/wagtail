import $ from 'jquery';

function createSnippetChooser(id, modelString) {
  const chooserElement = $('#' + id + '-chooser');
  const docTitle = chooserElement.find('.title');
  const input = $('#' + id);
  const editLink = chooserElement.find('.edit-link');
  const chooserBaseUrl = chooserElement.data('chooserUrl') + modelString + '/';

  /*
  Construct initial state of the chooser from the rendered (static) HTML and arguments passed to
  createSnippetChooser. State is either null (= no document chosen) or a dict of id, string and
  edit_link.

  The result returned from the snippet chooser modal (see wagtail.snippets.views.chooser.chosen)
  is a superset of this, and can therefore be passed directly to chooser.setState.
  */
  let state = null;
  if (input.val()) {
    state = {
      id: input.val(),
      edit_link: editLink.attr('href'),
      string: docTitle.text(),
    };
  }

  /* define public API functions for the chooser */
  const chooser = {
    getState: () => state,
    getValue: () => state && state.id,
    setState: (newState) => {
      if (newState) {
        input.val(newState.id);
        docTitle.text(newState.string);
        chooserElement.removeClass('blank');
        editLink.attr('href', newState.edit_link);
      } else {
        input.val('');
        chooserElement.addClass('blank');
      }

      state = newState;
    },
    openChooserModal: () => {
      // eslint-disable-next-line no-undef, new-cap
      ModalWorkflow({
        url: chooserBaseUrl,
        // eslint-disable-next-line no-undef
        onload: SNIPPET_CHOOSER_MODAL_ONLOAD_HANDLERS,
        responses: {
          snippetChosen: (result) => {
            chooser.setState(result);
          },
        },
      });
    },

    clear: () => {
      chooser.setState(null);
    },

  };

  $('.action-choose', chooserElement).on('click', () => {
    chooser.openChooserModal();
  });

  $('.action-clear', chooserElement).on('click', () => {
    chooser.clear();
  });

  return chooser;
}
window.createSnippetChooser = createSnippetChooser;
