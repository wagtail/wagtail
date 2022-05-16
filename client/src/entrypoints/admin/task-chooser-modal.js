import $ from 'jquery';
import { initTabs } from '../../includes/tabs';

const ajaxifyTaskCreateTab = (modal, jsonData) => {
  $(
    '#tab-new a.task-type-choice, #tab-new a.choose-different-task-type',
    modal.body,
  ).on('click', function onClickNew() {
    modal.loadUrl(this.href);
    return false;
  });

  // eslint-disable-next-line func-names
  $('form.task-create', modal.body).on('submit', function () {
    const formdata = new FormData(this);

    $.ajax({
      url: this.action,
      data: formdata,
      processData: false,
      contentType: false,
      type: 'POST',
      dataType: 'text',
      success: modal.loadResponseText,
      error(response, textStatus, errorThrown) {
        const message =
          jsonData.error_message +
          '<br />' +
          errorThrown +
          ' - ' +
          response.status;
        $('#tab-new', modal.body).append(
          '<div class="help-block help-critical">' +
            '<strong>' +
            jsonData.error_label +
            ': </strong>' +
            message +
            '</div>',
        );
      },
    });

    return false;
  });
};

const TASK_CHOOSER_MODAL_ONLOAD_HANDLERS = {
  chooser(modal, jsonData) {
    function ajaxifyLinks(context) {
      $('a.task-choice', context)
        // eslint-disable-next-line func-names
        .on('click', function () {
          modal.loadUrl(this.href);
          return false;
        });

      // eslint-disable-next-line func-names
      $('.pagination a', context).on('click', function () {
        // eslint-disable-next-line @typescript-eslint/no-use-before-define
        fetchResults(this.href);
        return false;
      });

      // Reinitialize tabs to hook up tab event listeners in the modal
      initTabs();
    }

    const searchForm = $('form.task-search', modal.body);
    const searchUrl = searchForm.attr('action');
    let request;

    function fetchResults(url, requestData) {
      var opts = {
        url: url,
        success(data) {
          request = null;
          $('#search-results').html(data);
          ajaxifyLinks($('#search-results'));
        },
        error() {
          request = null;
        },
      };
      if (requestData) {
        opts.data = requestData;
      }
      request = $.ajax(opts);
    }

    function search() {
      fetchResults(searchUrl, searchForm.serialize());
      return false;
    }

    ajaxifyLinks(modal.body);
    ajaxifyTaskCreateTab(modal, jsonData);

    $('form.task-search', modal.body).on('submit', search);

    // eslint-disable-next-line func-names
    $('#id_q').on('input', function () {
      if (request) {
        request.abort();
      }
      clearTimeout($.data(this, 'timer'));
      const wait = setTimeout(search, 50);
      $(this).data('timer', wait);
    });

    // eslint-disable-next-line func-names
    $('#id_task_type').on('change', function () {
      if (request) {
        request.abort();
      }
      clearTimeout($.data(this, 'timer'));
      const wait = setTimeout(search, 50);
      $(this).data('timer', wait);
    });
  },
  task_chosen(modal, jsonData) {
    modal.respond('taskChosen', jsonData.result);
    modal.close();
  },
  reshow_create_tab(modal, jsonData) {
    $('#tab-new', modal.body).html(jsonData.htmlFragment);
    ajaxifyTaskCreateTab(modal, jsonData);
  },
};
window.TASK_CHOOSER_MODAL_ONLOAD_HANDLERS = TASK_CHOOSER_MODAL_ONLOAD_HANDLERS;
