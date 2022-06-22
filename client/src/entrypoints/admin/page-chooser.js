import $ from 'jquery';

function createPageChooser(id, openAtParentId, options) {
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
  attributes in wagtailadmin/chooser/tables/page_title_cell.html) is a superset of this, and can
  therefore be passed directly to chooser.setState.
  */
  let state = null;
  if (input.val()) {
    state = {
      id: input.val(),
      parentId: openAtParentId,
      adminTitle: pageTitle.text(),
      editUrl: editLink.attr('href'),
    };
  }

  /* define public API functions for the chooser */
  const chooser = {
    getState: () => state,
    getValue: () => state && state.id,
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
    getTextLabel: (opts) => {
      if (!state) return null;
      const result = state.adminTitle;
      if (opts && opts.maxLength && result.length > opts.maxLength) {
        return result.substring(0, opts.maxLength - 1) + '…';
      }
      return result;
    },
    focus: () => {
      $('.action-choose', chooserElement).focus();
    },

    openChooserModal: () => {
      let url = chooserBaseUrl;
      if (state && state.parentId) {
        url += state.parentId + '/';
      }
      const urlParams = { page_type: options.model_names.join(',') };
      if (options.target_pages) {
        urlParams.target_pages = options.target_pages;
      }
      if (options.match_subclass) {
        urlParams.match_subclass = options.match_subclass;
      }
      if (options.can_choose_root) {
        urlParams.can_choose_root = 'true';
      }
      if (options.user_perms) {
        urlParams.user_perms = options.user_perms;
      }
      // eslint-disable-next-line no-undef
      ModalWorkflow({
        url: url,
        urlParams: urlParams,
        // eslint-disable-next-line no-undef
        onload: PAGE_CHOOSER_MODAL_ONLOAD_HANDLERS,
        responses: {
          pageChosen: (result) => {
            chooser.setState(result);
          },
        },
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
