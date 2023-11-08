/* A framework for modal popups that are loaded via AJAX, allowing navigation to other
subpages to happen within the lightbox, and returning a response to the calling page,
possibly after several navigation steps
*/

import $ from 'jquery';

import { noop } from '../../utils/noop';
import { gettext } from '../../utils/gettext';

/* eslint-disable */
function ModalWorkflow(opts) {
  /* options passed in 'opts':
    'url' (required): URL to the view that will be loaded into the dialog.
      If not provided and dialogId is given, the dialog component's data-url attribute is used instead.
    'dialogId' (optional): the id of the dialog component to use instead of the Bootstrap modal
    'responses' (optional): dict of callbacks to be called when the modal content
      calls modal.respond(callbackName, params)
    'onload' (optional): dict of callbacks to be called when loading a step of the workflow.
      The 'step' field in the response identifies the callback to call, passing it the
      modal object and response data as arguments
  */

  const self = {};
  const responseCallbacks = opts.responses || {};
  const errorCallback = opts.onError || noop;
  const useDialog = !!opts.dialogId;

  if (useDialog) {
    self.dialog = document.getElementById(opts.dialogId);
    self.url = opts.url || self.dialog.dataset.url;
    self.body = self.dialog.querySelector('[data-w-dialog-target]');

    // Clear the dialog body as it may have been populated previously
    self.body.innerHTML = '';
  } else {
    /* remove any previous modals before continuing (closing doesn't remove them from the dom) */
    $('body > .modal').remove();

    // disable the trigger element so it cannot be clicked twice while modal is loading
    self.triggerElement = document.activeElement;
    self.triggerElement.setAttribute('disabled', true);

    // set default contents of container
    const iconClose =
      '<svg class="icon icon-cross" aria-hidden="true"><use href="#icon-cross"></use></svg>';
    self.container = $(
      '<div class="modal fade" tabindex="-1" role="dialog" aria-hidden="true">\n  <div class="modal-dialog">\n    <div class="modal-content">\n      <button type="button" class="button close button--icon text-replace" data-dismiss="modal">' +
        iconClose +
        gettext('Close') +
        '</button>\n      <div class="modal-body"></div>\n    </div><!-- /.modal-content -->\n  </div><!-- /.modal-dialog -->\n</div>',
    );

    // add container to body and hide it, so content can be added to it before display
    $('body').append(self.container);
    self.container.modal('hide');

    // add listener - once modal is about to be hidden, re-enable the trigger unless it's been forcibly
    // disabled by adding a `data-force-disabled` attribute; this mechanism is necessary to accommodate
    // response handlers that disable the trigger to prevent it from reopening
    self.container.on('hide.bs.modal', () => {
      if (!self.triggerElement.hasAttribute('data-force-disabled')) {
        self.triggerElement.removeAttribute('disabled');
      }
    });

    // add listener - once modal is fully hidden (closed & css transitions end) - re-focus on trigger and remove from DOM
    self.container.on('hidden.bs.modal', function () {
      self.triggerElement.focus();
      self.container.remove();
    });

    self.url = opts.url;
    self.body = self.container.find('.modal-body');
  }

  self.loadUrl = function (url, urlParams) {
    $.get(url, urlParams, self.loadResponseText, 'text').fail(errorCallback);
  };

  self.postForm = function (url, formData) {
    $.post(url, formData, self.loadResponseText, 'text').fail(errorCallback);
  };

  self.ajaxifyForm = function (formSelector) {
    $(formSelector).each(function () {
      const action = this.action;
      if (this.method.toLowerCase() === 'get') {
        $(this).on('submit', function () {
          self.loadUrl(action, $(this).serialize());
          return false;
        });
      } else {
        $(this).on('submit', function () {
          self.postForm(action, $(this).serialize());
          return false;
        });
      }
    });
  };

  self.loadResponseText = function (responseText) {
    const response = JSON.parse(responseText);
    self.loadBody(response);
  };

  self.loadBody = function (response) {
    if (response.html) {
      // if response contains an 'html' item, replace modal body with it
      if (useDialog) {
        self.body.innerHTML = response.html;
      } else {
        self.body.html(response.html);
        self.container.modal('show');
      }
    }

    /* If response contains a 'step' identifier, and that identifier is found in
    the onload dict, call that onload handler */
    if (opts.onload && response.step && response.step in opts.onload) {
      opts.onload[response.step](self, response);
    }
  };

  self.respond = function (responseType) {
    if (responseType in responseCallbacks) {
      const args = Array.prototype.slice.call(arguments, 1);
      responseCallbacks[responseType].apply(self, args);
    }
  };

  self.close = function () {
    if (useDialog) {
      self.dialog.dispatchEvent(new CustomEvent('w-dialog:hide'));
    } else {
      self.container.modal('hide');
    }
  };

  self.loadUrl(self.url, opts.urlParams);

  return self;
}
window.ModalWorkflow = ModalWorkflow;
