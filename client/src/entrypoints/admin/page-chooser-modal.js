import $ from 'jquery';
import { ChooserModal } from '../../includes/chooserModal';

const PAGE_CHOOSER_MODAL_ONLOAD_HANDLERS = {
  browse(modal, jsonData) {
    /* Set up link-types links to open in the modal */
    // eslint-disable-next-line func-names
    $('.link-types a', modal.body).on('click', function () {
      modal.loadUrl(this.href);
      return false;
    });

    /* Set up dropdown links to open in the modal */
    // eslint-disable-next-line func-names
    $('[data-locale-selector-link]', modal.body).on('click', function () {
      modal.loadUrl(this.href);
      return false;
    });

    /* Set up submissions of the search form to open in the modal. */
    modal.ajaxifyForm($('form.search-form', modal.body));

    /* Set up search-as-you-type behaviour on the search box */
    const searchUrl = $('form.search-form', modal.body).attr('action');

    /* save initial page browser HTML, so that we can restore it if the search box gets cleared */
    const initialPageResultsHtml = $('.page-results', modal.body).html();

    // Set up submissions of the "choose multiple items" form to open in the modal.
    modal.ajaxifyForm($('form[data-multiple-choice-form]', modal.body));

    let request;

    function search() {
      const query = $('#id_q', modal.body).val();
      if (query !== '') {
        request = $.ajax({
          url: searchUrl,
          data: {
            // eslint-disable-next-line id-length
            q: query,
          },
          success(data) {
            request = null;
            $('.page-results', modal.body).html(data);
            // eslint-disable-next-line @typescript-eslint/no-use-before-define
            ajaxifySearchResults();
          },
          error() {
            request = null;
          },
        });
      } else {
        /* search box is empty - restore original page browser HTML */
        $('.page-results', modal.body).html(initialPageResultsHtml);
        // eslint-disable-next-line @typescript-eslint/no-use-before-define
        ajaxifyBrowseResults();
      }
      return false;
    }

    // eslint-disable-next-line func-names
    $('#id_q', modal.body).on('input', function () {
      if (request) {
        request.abort();
      }
      clearTimeout($.data(this, 'timer'));
      const wait = setTimeout(search, 200);
      $(this).data('timer', wait);
    });

    function updateMultipleChoiceSubmitEnabledState() {
      // update the enabled state of the multiple choice submit button depending on whether
      // any items have been selected
      if ($('[data-multiple-choice-select]:checked', modal.body).length) {
        $('[data-multiple-choice-submit]', modal.body).removeAttr('disabled');
      } else {
        $('[data-multiple-choice-submit]', modal.body).attr('disabled', true);
      }
    }

    /* Set up behaviour of choose-page links in the newly-loaded search results,
    to pass control back to the calling page */
    function ajaxifySearchResults() {
      // eslint-disable-next-line func-names
      $('.page-results a.choose-page', modal.body).on('click', function () {
        const pageData = $(this).data();
        modal.respond('pageChosen', pageData);
        modal.close();

        return false;
      });
      /* pagination links within search results should be AJAX-fetched
      and the result loaded into .page-results (and ajaxified) */
      $(
        '.page-results a.navigate-pages, .page-results [data-w-breadcrumbs-target~="content"] a',
        modal.body,
      ).on('click', function handleLinkClick() {
        $('.page-results', modal.body).load(this.href, ajaxifySearchResults);
        return false;
      });
      /* Set up parent navigation links (.navigate-parent) to open in the modal */
      // eslint-disable-next-line func-names
      $('.page-results a.navigate-parent', modal.body).on('click', function () {
        modal.loadUrl(this.href);
        return false;
      });

      updateMultipleChoiceSubmitEnabledState();
      $('[data-multiple-choice-select]', modal.body).on('change', () => {
        updateMultipleChoiceSubmitEnabledState();
      });
    }

    function ajaxifyBrowseResults() {
      /* Set up page navigation links to open in the modal */
      $(
        '.page-results a.navigate-pages, .page-results [data-w-breadcrumbs-target~="content"] a',
        modal.body,
      ).on('click', function handleLinkClick() {
        modal.loadUrl(this.href);
        return false;
      });

      /* Set up behaviour of choose-page links, to pass control back to the calling page */
      // eslint-disable-next-line func-names
      $('a.choose-page', modal.body).on('click', function () {
        const pageData = $(this).data();
        pageData.parentId = jsonData.parent_page_id;
        modal.respond('pageChosen', pageData);
        modal.close();

        return false;
      });
      // eslint-disable-next-line func-names
      $('[data-locale-selector-link]', modal.body).on('click', function () {
        modal.loadUrl(this.href);
        return false;
      });

      updateMultipleChoiceSubmitEnabledState();
      $('[data-multiple-choice-select]', modal.body).on('change', () => {
        updateMultipleChoiceSubmitEnabledState();
      });
    }
    ajaxifyBrowseResults();

    /*
    Focus on the search box when opening the modal.
    FIXME: this doesn't seem to have any effect (at least on Chrome)
    */
    $('#id_q', modal.body).trigger('focus');
  },

  anchor_link(modal) {
    // eslint-disable-next-line func-names
    $('p.link-types a', modal.body).on('click', function () {
      modal.loadUrl(this.href);
      return false;
    });

    // eslint-disable-next-line func-names
    $('form', modal.body).on('submit', function () {
      modal.postForm(this.action, $(this).serialize());
      return false;
    });
  },
  email_link(modal) {
    // eslint-disable-next-line func-names
    $('p.link-types a', modal.body).on('click', function () {
      modal.loadUrl(this.href);
      return false;
    });

    // eslint-disable-next-line func-names
    $('form', modal.body).on('submit', function () {
      modal.postForm(this.action, $(this).serialize());
      return false;
    });
  },
  phone_link(modal) {
    // eslint-disable-next-line func-names
    $('p.link-types a', modal.body).on('click', function () {
      modal.loadUrl(this.href);
      return false;
    });

    // eslint-disable-next-line func-names
    $('form', modal.body).on('submit', function () {
      modal.postForm(this.action, $(this).serialize());
      return false;
    });
  },
  external_link(modal) {
    // eslint-disable-next-line func-names
    $('p.link-types a', modal.body).on('click', function () {
      modal.loadUrl(this.href);
      return false;
    });

    // eslint-disable-next-line func-names
    $('form', modal.body).on('submit', function () {
      modal.postForm(this.action, $(this).serialize());
      return false;
    });
  },
  external_link_chosen(modal, jsonData) {
    modal.respond('pageChosen', jsonData.result);
    modal.close();
  },
  page_chosen(modal, jsonData) {
    modal.respond('pageChosen', jsonData.result);
    modal.close();
  },
  confirm_external_to_internal(modal, jsonData) {
    // eslint-disable-next-line func-names, prefer-arrow-callback
    $('[data-action-confirm]', modal.body).on('click', function () {
      modal.respond('pageChosen', jsonData.internal);
      modal.close();
      return false;
    });
    // eslint-disable-next-line func-names, prefer-arrow-callback
    $('[data-action-deny]', modal.body).on('click', function () {
      modal.respond('pageChosen', jsonData.external);
      modal.close();
      return false;
    });
  },
};
window.PAGE_CHOOSER_MODAL_ONLOAD_HANDLERS = PAGE_CHOOSER_MODAL_ONLOAD_HANDLERS;

class PageChooserModal extends ChooserModal {
  onloadHandlers = PAGE_CHOOSER_MODAL_ONLOAD_HANDLERS;
  chosenResponseName = 'pageChosen';

  getURL(opts) {
    let url = super.getURL();
    if (opts.parentId) {
      url += opts.parentId + '/';
    }
    return url;
  }

  getURLParams(opts) {
    const urlParams = super.getURLParams(opts);
    urlParams.page_type = opts.modelNames.join(',');
    if (opts.targetPages) {
      urlParams.target_pages = opts.targetPages;
    }
    if (opts.matchSubclass) {
      urlParams.match_subclass = opts.matchSubclass;
    }
    if (opts.canChooseRoot) {
      urlParams.can_choose_root = 'true';
    }
    if (opts.userPerms) {
      urlParams.user_perms = opts.userPerms;
    }
    return urlParams;
  }
}
window.PageChooserModal = PageChooserModal;
