import $ from 'jquery';

const TASK_CHOOSER_MODAL_ONLOAD_HANDLERS = {
  chooser(modal, jsonData) {
    function ajaxifyLinks(context) {
      $('a.task-type-choice, a.choose-different-task-type, a.task-choice', context)
        // eslint-disable-next-line func-names
        .on('click', function () {
          modal.loadUrl(this.href);
          return false;
        });

      // eslint-disable-next-line func-names
      $('.pagination a', context).on('click', function () {
        const page = this.getAttribute('data-page');
        // eslint-disable-next-line @typescript-eslint/no-use-before-define
        setPage(page);
        return false;
      });

      $('a.create-one-now').on('click', (e) => {
        // Select upload form tab
        $('a[href="#new"]').tab('show');
        e.preventDefault();
      });
    }

    const searchUrl = $('form.task-search', modal.body).attr('action');
    let request;
    function search() {
      request = $.ajax({
        url: searchUrl,
        data: {
          // eslint-disable-next-line id-length
          q: $('#id_q').val(),
          task_type: $('#id_task_type').val(),
        },
        success(data) {
          request = null;
          $('#search-results').html(data);
          ajaxifyLinks($('#search-results'));
        },
        error() {
          request = null;
        }
      });
      return false;
    }
    function setPage(page) {
      let dataObj;

      if ($('#id_q').val().length) {
        // eslint-disable-next-line id-length
        dataObj = { q: $('#id_q').val(), p: page };
      } else {
        // eslint-disable-next-line id-length
        dataObj = { p: page };
      }

      request = $.ajax({
        url: searchUrl,
        data: dataObj,
        success(data) {
          request = null;
          $('#search-results').html(data);
          ajaxifyLinks($('#search-results'));
        },
        error() {
          request = null;
        }
      });
      return false;
    }

    ajaxifyLinks(modal.body);

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
          const message = jsonData.error_message + '<br />' + errorThrown + ' - ' + response.status;
          $('#new').append(
            '<div class="help-block help-critical">' +
            '<strong>' + jsonData.error_label + ': </strong>' + message + '</div>');
        }
      });

      return false;
    });

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
  }
};
window.TASK_CHOOSER_MODAL_ONLOAD_HANDLERS = TASK_CHOOSER_MODAL_ONLOAD_HANDLERS;
