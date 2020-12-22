/* A framework for modal popups that are loaded via AJAX, allowing navigation to other
subpages to happen within the lightbox, and returning a response to the calling page,
possibly after several navigation steps
*/

import $ from 'jquery';

/* global wagtailConfig */

/* eslint-disable */
function ModalWorkflow(opts) {
  /* options passed in 'opts':
    'url' (required): initial
    'responses' (optional): dict of callbacks to be called when the modal content
      calls modal.respond(callbackName, params)
    'onload' (optional): dict of callbacks to be called when loading a step of the workflow.
      The 'step' field in the response identifies the callback to call, passing it the
      modal object and response data as arguments
  */

  const self = {};
  const responseCallbacks = opts.responses || {};
  // eslint-disable-next-line func-names
  const errorCallback = opts.onError || function () {};

  /* remove any previous modals before continuing (closing doesn't remove them from the dom) */
  $('body > .modal').remove();

  // set default contents of container
  // eslint-disable-next-line max-len
  const iconClose = '<svg class="icon icon-cross" aria-hidden="true" focusable="false"><use href="#icon-cross"></use></svg>';
  // eslint-disable-next-line max-len
  const container = $('<div class="modal fade" tabindex="-1" role="dialog" aria-hidden="true">\n  <div class="modal-dialog">\n    <div class="modal-content">\n      <button type="button" class="button close button--icon text-replace" data-dismiss="modal">' + iconClose + wagtailConfig.STRINGS.CLOSE + '</button>\n      <div class="modal-body"></div>\n    </div><!-- /.modal-content -->\n  </div><!-- /.modal-dialog -->\n</div>');

  // add container to body and hide it, so content can be added to it before display
  $('body').append(container);
  container.modal('hide');

  self.body = container.find('.modal-body');

  // eslint-disable-next-line func-names
  self.loadUrl = function (url, urlParams) {
    $.get(url, urlParams, self.loadResponseText, 'text').fail(errorCallback);
  };

  // eslint-disable-next-line func-names
  self.postForm = function (url, formData) {
    $.post(url, formData, self.loadResponseText, 'text').fail(errorCallback);
  };

  // eslint-disable-next-line func-names
  self.ajaxifyForm = function (formSelector) {
    // eslint-disable-next-line func-names
    $(formSelector).each(function () {
      const action = this.action;
      if (this.method.toLowerCase() === 'get') {
        // eslint-disable-next-line func-names
        $(this).on('submit', function () {
          self.loadUrl(action, $(this).serialize());
          return false;
        });
      } else {
        // eslint-disable-next-line func-names
        $(this).on('submit', function () {
          self.postForm(action, $(this).serialize());
          return false;
        });
      }
    });
  };

  // eslint-disable-next-line func-names
  self.loadResponseText = function (responseText) {
    const response = JSON.parse(responseText);
    self.loadBody(response);
  };

  // eslint-disable-next-line func-names
  self.loadBody = function (response) {
    if (response.html) {
      // if response contains an 'html' item, replace modal body with it
      self.body.html(response.html);
      container.modal('show');
    }

    /* If response contains a 'step' identifier, and that identifier is found in
    the onload dict, call that onload handler */
    if (opts.onload && response.step && (response.step in opts.onload)) {
      opts.onload[response.step](self, response);
    }
  };

  // eslint-disable-next-line func-names
  self.respond = function (responseType) {
    if (responseType in responseCallbacks) {
      // eslint-disable-next-line prefer-rest-params
      const args = Array.prototype.slice.call(arguments, 1);
      responseCallbacks[responseType].apply(self, args);
    }
  };

  // eslint-disable-next-line func-names
  self.close = function () {
    container.modal('hide');
  };

  self.loadUrl(opts.url, opts.urlParams);

  return self;
}
window.ModalWorkflow = ModalWorkflow;
