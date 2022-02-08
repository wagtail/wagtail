import $ from 'jquery';

function createDocumentChooser(id) {
  const chooserElement = $('#' + id + '-chooser');
  const docTitle = chooserElement.find('.title');
  const input = $('#' + id);
  const editLink = chooserElement.find('.edit-link');
  const chooserBaseUrl = chooserElement.data('chooserUrl');

  /*
  Construct initial state of the chooser from the rendered (static) HTML and arguments passed to
  createDocumentChooser. State is either null (= no document chosen) or a dict of id, title and
  edit_link.

  The result returned from the document chooser modal (see get_document_chosen_response in
  wagtail.documents.views.chooser) is a superset of this, and can therefore be passed directly to
  chooser.setState.
  */
  let state = null;
  if (input.val()) {
    state = {
      id: input.val(),
      edit_link: editLink.attr('href'),
      title: docTitle.text(),
    };
  }

  /* define public API functions for the chooser */
  const chooser = {
    getState: () => state,
    getValue: () => state && state.id,
    setState: (newState) => {
      if (newState) {
        input.val(newState.id);
        docTitle.text(newState.title);
        chooserElement.removeClass('blank');
        editLink.attr('href', newState.edit_link);
      } else {
        input.val('');
        chooserElement.addClass('blank');
      }

      state = newState;
    },
    getTextLabel: (opts) => {
      if (!state) return null;
      const result = state.title;
      if (opts && opts.maxLength && result.length > opts.maxLength) {
        return result.substring(0, opts.maxLength - 1) + '…';
      }
      return result;
    },
    focus: () => {
      $('.action-choose', chooserElement).focus();
    },
    openChooserModal: () => {
      // eslint-disable-next-line no-undef
      ModalWorkflow({
        url: chooserBaseUrl,
        // eslint-disable-next-line no-undef
        onload: DOCUMENT_CHOOSER_MODAL_ONLOAD_HANDLERS,
        responses: {
          documentChosen: (result) => {
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
window.createDocumentChooser = createDocumentChooser;
