import $ from 'jquery';
import { initTooltips } from '../../includes/initTooltips';

/* global wagtail */

const PAGE_CHOOSER_MODAL_ONLOAD_HANDLERS = {
  browse(modal, jsonData) {
    /* Set up link-types links to open in the modal */
    // eslint-disable-next-line func-names
    $('.link-types a', modal.body).on('click', function () {
      modal.loadUrl(this.href);
      return false;
    });

    /* Initialize dropdowns */
    wagtail.ui.initDropDowns();
    /* Set up dropdown links to open in the modal */
    // eslint-disable-next-line func-names
    $('.c-dropdown__item .u-link', modal.body).on('click', function () {
      modal.loadUrl(this.href);
      return false;
    });

    /*
    Set up submissions of the search form to open in the modal.

    FIXME: wagtailadmin.views.chooser.browse doesn't actually return a modal-workflow
    response for search queries, so this just fails with a JS error.
    Luckily, the search-as-you-type logic below means that we never actually need to
    submit the form to get search results, so this has the desired effect of preventing
    plain vanilla form submissions from completing (which would clobber the entire
    calling page, not just the modal). It would be nice to do that without throwing
    a JS error, that's all...
    */
    modal.ajaxifyForm($('form.search-form', modal.body));

    /* Set up search-as-you-type behaviour on the search box */
    const searchUrl = $('form.search-form', modal.body).attr('action');

    /* save initial page browser HTML, so that we can restore it if the search box gets cleared */
    const initialPageResultsHtml = $('.page-results', modal.body).html();

    let request;

    function search() {
      const query = $('#id_q', modal.body).val();
      if (query !== '') {
        request = $.ajax({
          url: searchUrl,
          data: {
            // eslint-disable-next-line id-length
            q: query,
            results_only: true,
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
        '.page-results a.navigate-pages, .page-results [data-breadcrumb-item] a',
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
    }

    function ajaxifyBrowseResults() {
      /* Set up page navigation links to open in the modal */
      $(
        '.page-results a.navigate-pages, .page-results [data-breadcrumb-item] a',
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
      $('.c-dropdown__item .u-link', modal.body).on('click', function () {
        modal.loadUrl(this.href);
        return false;
      });

      wagtail.ui.initDropDowns();
    }
    ajaxifyBrowseResults();
    initTooltips();

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
