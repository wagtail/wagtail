import $ from 'jquery';

function createPageChooser(id, openAtParentId, config) {
  const chooserElement = $('#' + id + '-chooser');
  const pageTitle = chooserElement.find('.title');
  const input = $('#' + id);
  const editLink = chooserElement.find('.edit-link');
  const chooserBaseUrl = chooserElement.data('chooserUrl');

  /*
  Construct initial state of the chooser from the rendered (static) HTML and arguments passed to
  createPageChooser. State is either null (= no page chosen) or a dict of id, parentId,
  adminTitle (the admin display title) and editUrl.
  The result returned from the page chooser modal (which is ultimately built from the data
  attributes in wagtailadmin/pages/listing/_page_title_choose.html) is a superset of this, and
  can therefore be passed directly to chooser.setState.
  */
  let state = null;
  if (input.val()) {
    state = {
      id: input.val(),
      parentId: openAtParentId,
      adminTitle: pageTitle.text(),
      editUrl: editLink.attr('href')
    };
  }

  /* define public API functions for the chooser */
  const chooser = {
    getState: () => state,
    getValue: () => state.id,
    setState: (newState) => {
      if (newState) {
        input.val(newState.id);
        pageTitle.text(newState.adminTitle);
        chooserElement.removeClass('blank');
        editLink.attr('href', newState.editUrl);
      } else {
        input.val('');
        chooserElement.addClass('blank');
      }

      state = newState;
    },

    openChooserModal: () => {
      let url = chooserBaseUrl;
      if (state && state.parentId) {
        url += state.parentId + '/';
      }
      const urlParams = { page_type: config.model_names.join(',') };
      if (config.can_choose_root) {
        urlParams.can_choose_root = 'true';
      }
      if (config.user_perms) {
        urlParams.user_perms = config.user_perms;
      }
      // eslint-disable-next-line no-undef, new-cap
      ModalWorkflow({
        url: url,
        urlParams: urlParams,
        // eslint-disable-next-line no-undef
        onload: PAGE_CHOOSER_MODAL_ONLOAD_HANDLERS,
        responses: {
          pageChosen: (result) => {
            chooser.setState(result);
          }
        }
      });
    },

    clear: () => {
      chooser.setState(null);
    },
  };

  /* hook up chooser API to the buttons */
  $('.action-choose', chooserElement).on('click', () => {
    chooser.openChooserModal();
  });

  $('.action-clear', chooserElement).on('click', () => {
    chooser.clear();
  });

  return chooser;
}
window.createPageChooser = createPageChooser;
